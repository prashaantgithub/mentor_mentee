from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, Response
from flask_login import login_required, current_user
from ..utils import role_required, timestamp_to_local
from ..utils import report_generator
from .. import db
from ..models import (User, Class, Batch, MenteeProfile, MentorProfile, MentorAssignment, Session,
                     PlacementInformation, ResearchRecord, AcademicSemesterMarkDetails, 
                     MentorMeetingDetails, AwardsAndAchievements, CocurricularActivityRecord, 
                     ExtracurricularActivityRecord, InternshipInformation, HonorsMinorMarksDetails,
                     AttendanceRecord, LeaveRequest)
import pandas as pd
import math
import re
from datetime import datetime, timedelta, timezone, date
import pytz
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

LOCAL_TIMEZONE = pytz.timezone('Asia/Kolkata')

def is_third_saturday(d):
    return d.weekday() == 5 and 15 <= d.day <= 21

def model_to_dict(model_instance):
    d = {}
    for column in model_instance.__table__.columns:
        val = getattr(model_instance, column.name)
        if isinstance(val, (datetime, date)):
            d[column.name] = val.isoformat()
        else:
            d[column.name] = val
    return d

def check_for_collision(mentor_id, session_datetimes, existing_assignment_id=None):
    query = Session.query.join(MentorAssignment).filter(
        MentorAssignment.mentor_id == mentor_id,
        Session.start_time.in_(session_datetimes)
    )
    if existing_assignment_id:
        query = query.filter(MentorAssignment.id != existing_assignment_id)
    
    existing_session = query.first()

    if existing_session:
        colliding_batch = existing_session.assignment.batch
        colliding_class = colliding_batch.class_model
        return f"Schedule conflict detected! Mentor is already assigned to {colliding_class.name} - {colliding_batch.name} at one of the selected times."
    return None

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
@role_required('admin')
def view_users():
    departments = db.session.query(MenteeProfile.department).distinct().filter(MenteeProfile.department.isnot(None)).order_by(MenteeProfile.department).all()
    departments = [d[0] for d in departments]
    
    classes = Class.query.order_by(Class.name).all()
    
    return render_template('admin/view_users.html', departments=departments, classes=classes)

@admin_bp.route('/mentee/<int:user_id>')
@login_required
@role_required('admin')
def view_mentee_profile(user_id):
    mentee_user = User.query.filter_by(id=user_id, role='mentee').first_or_404()
    return render_template('admin/view_mentee_profile.html', mentee_user=mentee_user)

@admin_bp.route('/mentor/<int:user_id>')
@login_required
@role_required('admin')
def view_mentor_profile(user_id):
    mentor_user = User.query.filter_by(id=user_id, role='mentor').first_or_404()
    assignments = MentorAssignment.query.filter_by(mentor_id=user_id, is_active=True).all()
    return render_template('admin/view_mentor_profile.html', mentor_user=mentor_user, assignments=assignments)


@admin_bp.route('/mentee/<int:user_id>/download_report')
@login_required
@role_required('admin')
def download_mentee_report(user_id):
    pdf_bytes, filename = report_generator.generate_mentee_full_report(user_id)
    if pdf_bytes is None:
        flash("Could not generate report for this mentee.", "danger")
        return redirect(url_for('admin.view_mentee_profile', user_id=user_id))
    
    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment;filename={filename}'
    return response

@admin_bp.route('/manage_mentors', methods=['GET'])
@login_required
@role_required('admin')
def manage_mentors():
    mentors = User.query.filter_by(role='mentor').order_by(User.name).all()
    return render_template('admin/manage_mentors.html', mentors=mentors)

@admin_bp.route('/mentor/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_mentor(user_id):
    mentor = User.query.filter_by(id=user_id, role='mentor').first_or_404()
    try:
        db.session.delete(mentor)
        db.session.commit()
        flash(f"Mentor '{mentor.name}' has been deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting mentor: {e}", 'danger')
    return redirect(url_for('admin.manage_mentors'))

@admin_bp.route('/mentors/delete_all', methods=['POST'])
@login_required
@role_required('admin')
def delete_all_mentors():
    try:
        num_deleted = User.query.filter_by(role='mentor').delete()
        db.session.commit()
        flash(f"Successfully deleted {num_deleted} mentor(s).", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting all mentors: {e}", 'danger')
    return redirect(url_for('admin.manage_mentors'))

@admin_bp.route('/upload_review_mentors', methods=['POST'])
@login_required
@role_required('admin')
def upload_review_mentors():
    file = request.files.get('mentor_file')
    if not file or not file.filename.endswith(('.csv', '.xlsx')):
        flash("Please upload a valid CSV or Excel file.", "danger")
        return redirect(url_for('admin.manage_mentors'))

    try:
        df = pd.read_csv(file, dtype=str) if file.filename.endswith('.csv') else pd.read_excel(file, dtype=str)
        df.columns = [col.strip() for col in df.columns]

        if 'Level' in df.columns and 'level' not in df.columns:
            df.rename(columns={'Level': 'level'}, inplace=True)

        required_columns = {'Name', 'level', 'Email'}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            flash(f"File is missing required columns: {', '.join(missing_cols)}", "danger")
            return redirect(url_for('admin.manage_mentors'))
    except Exception as e:
        flash(f"Error reading file: {e}", "danger")
        return redirect(url_for('admin.manage_mentors'))

    df.dropna(how='all', inplace=True)
    df.fillna('', inplace=True)

    existing_mentor_emails_db = {item[0].lower() for item in User.query.filter_by(role='mentor').with_entities(User.email).all()}
    
    valid_mentors, invalid_rows, db_duplicates = [], [], []
    seen_emails_in_file = set()

    for index, row in df.iterrows():
        errors = []
        name = row.get('Name', '').strip()
        level = row.get('level', '').strip().upper()
        email = row.get('Email', '').strip().lower()

        if not name: errors.append("Name is missing.")
        if any(char.isdigit() for char in name): errors.append("Name cannot contain numbers.")
        
        if not level: errors.append("Level is missing.")
        if level not in ['BTECH', 'MTECH']: errors.append("Level must be 'BTECH' or 'MTECH'.")
        
        if not email: errors.append("Email is missing.")
        elif '@' not in email or '.' not in email.split('@')[1]: errors.append("Invalid email format.")
        
        if email:
            if email in seen_emails_in_file: errors.append("Email is duplicated in this file.")
            seen_emails_in_file.add(email)
            if email in existing_mentor_emails_db:
                db_duplicates.append({'Name': name, 'level': level, 'Email': email})
                continue

        mentor_data = {'Name': name, 'level': level, 'Email': email}
        
        if errors:
            invalid_rows.append({'data': mentor_data, 'errors': errors})
        else:
            valid_mentors.append(mentor_data)
            
    session['valid_mentors_to_import'] = valid_mentors
    
    return render_template('admin/confirm_mentor_import.html', 
                           valid_mentors=valid_mentors,
                           invalid_rows=invalid_rows,
                           db_duplicates=db_duplicates)

@admin_bp.route('/confirm_mentor_import', methods=['POST'])
@login_required
@role_required('admin')
def confirm_mentor_import():
    mentors_to_import = session.get('valid_mentors_to_import', [])

    if not mentors_to_import:
        flash("No valid mentor data to import or session expired.", "danger")
        return redirect(url_for('admin.manage_mentors'))
    
    try:
        for mentor_data in mentors_to_import:
            email = mentor_data.get('Email').lower()
            user = User(
                email=email,
                name=mentor_data.get('Name'),
                role='mentor',
                must_change_password=True
            )
            user.set_password(email)

            mentor_profile = MentorProfile(
                user=user,
                level=mentor_data['level'],
                profile_complete=False
            )
            db.session.add(user)
        
        db.session.commit()
        flash(f"{len(mentors_to_import)} new mentors have been successfully imported.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during import: {e}", "danger")
    finally:
        session.pop('valid_mentors_to_import', None)

    return redirect(url_for('admin.manage_mentors'))

@admin_bp.route('/manage_classes', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_classes():
    if request.method == 'POST':
        class_name = request.form.get('class_name', '').strip()
        if not class_name:
            flash("Class name cannot be empty.", "danger")
        elif Class.query.filter(Class.name.ilike(class_name)).first():
            flash(f"Class '{class_name}' already exists.", "danger")
        else:
            new_class = Class(name=class_name)
            db.session.add(new_class)
            db.session.commit()
            flash(f"Class '{class_name}' created successfully.", "success")
        return redirect(url_for('admin.manage_classes'))
    
    classes_query = Class.query.filter_by(is_archived=False).order_by(Class.name).all()
    
    classes_with_status = []
    for c in classes_query:
        total_batches = c.batches.count()
        unassigned_batches = sum(1 for batch in c.batches if not batch.mentor_assignment)
        classes_with_status.append({
            'class_obj': c,
            'unassigned_count': unassigned_batches
        })

    return render_template('admin/manage_classes.html', classes_with_status=classes_with_status)

@admin_bp.route('/class/<int:class_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_class(class_id):
    target_class = Class.query.get_or_404(class_id)
    try:
        db.session.delete(target_class)
        db.session.commit()
        flash(f"Class '{target_class.name}' and all its associated data have been deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting class: {e}", 'danger')
    return redirect(url_for('admin.manage_classes'))


@admin_bp.route('/class/<int:class_id>/manage', methods=['GET'])
@login_required
@role_required('admin')
def manage_class(class_id):
    target_class = Class.query.get_or_404(class_id)
    unbatched_students = MenteeProfile.query.filter_by(class_id=class_id, batch_id=None).join(User).order_by(User.name).all()
    created_batches = Batch.query.filter_by(class_id=class_id).order_by(Batch.name).all()
    
    now_utc = datetime.now(timezone.utc)
    upcoming_sessions_map = {}
    for batch in created_batches:
        if batch.mentor_assignment:
            sessions = Session.query.filter(
                Session.mentor_assignment_id == batch.mentor_assignment.id,
                Session.start_time >= now_utc,
                Session.status.in_(['Upcoming', 'In Progress'])
            ).order_by(Session.start_time.asc()).all()
            upcoming_sessions_map[batch.id] = sessions

    return render_template('admin/manage_class.html', 
                           target_class=target_class, 
                           unbatched_students=unbatched_students, 
                           batches=created_batches,
                           upcoming_sessions_map=upcoming_sessions_map)

@admin_bp.route('/class/<int:class_id>/assign_mentor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def assign_mentor(class_id):
    target_class = Class.query.get_or_404(class_id)

    if request.method == 'POST':
        mentor_id = int(request.form.get('mentor_id'))
        batch_id = int(request.form.get('batch_id'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        day_of_week = int(request.form.get('day_of_week'))
        session_time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        num_weeks = int(request.form.get('num_weeks'))

        mentor = User.query.get(mentor_id)
        batch = Batch.query.get(batch_id)

        current_mentee_count = db.session.query(func.count(MenteeProfile.id)).join(Batch).join(MentorAssignment).filter(MentorAssignment.mentor_id == mentor_id, MentorAssignment.is_active == True).scalar()
        batch_mentee_count = batch.mentees.count()
        if (current_mentee_count + batch_mentee_count) > 45:
            flash(f"Assignment failed: Mentor {mentor.name} has {current_mentee_count} mentees. Assigning this batch of {batch_mentee_count} would exceed the 45 mentee limit.", "danger")
            return redirect(url_for('admin.assign_mentor', class_id=class_id))

        existing_assignment_in_class = MentorAssignment.query.join(Batch).filter(MentorAssignment.mentor_id == mentor_id, Batch.class_id == class_id, MentorAssignment.is_active == True).first()
        if existing_assignment_in_class:
            flash(f"Assignment failed: Mentor {mentor.name} is already assigned to batch {existing_assignment_in_class.batch.name} in this class.", "danger")
            return redirect(url_for('admin.assign_mentor', class_id=class_id))
        
        days_ahead = (day_of_week - start_date.weekday() + 7) % 7
        current_date = start_date + timedelta(days=days_ahead)
        sessions_to_create_dates = []
        while len(sessions_to_create_dates) < num_weeks:
            if not is_third_saturday(current_date):
                sessions_to_create_dates.append(current_date)
            current_date += timedelta(weeks=1)
        
        session_datetimes = [LOCAL_TIMEZONE.localize(datetime.combine(d, session_time)).astimezone(timezone.utc) for d in sessions_to_create_dates]

        collision_message = check_for_collision(mentor_id, session_datetimes)
        if collision_message:
            flash(collision_message, "danger")
            return redirect(url_for('admin.assign_mentor', class_id=class_id))
        
        try:
            new_assignment = MentorAssignment(mentor_id=mentor_id, batch_id=batch_id, is_active=True)
            db.session.add(new_assignment)

            for i, dt in enumerate(session_datetimes):
                new_session = Session(session_number=i + 1, start_time=dt, status='Upcoming')
                new_assignment.sessions.append(new_session)
            
            db.session.commit()
            flash(f"Successfully assigned {mentor.name} to {batch.name} and scheduled {num_weeks} sessions.", "success")
            return redirect(url_for('admin.manage_class', class_id=class_id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during assignment: {e}", "danger")

    mentors_with_data = []
    mentors = User.query.filter_by(role='mentor', is_active=True).order_by(User.name).all()
    for mentor in mentors:
        mentee_count = db.session.query(func.count(MenteeProfile.id)).join(Batch).join(MentorAssignment).filter(MentorAssignment.mentor_id == mentor.id, MentorAssignment.is_active == True).scalar()
        assigned_classes = [a.batch.class_model.id for a in mentor.mentor_profile.assignments.filter_by(is_active=True).all()]
        mentors_with_data.append({'mentor': mentor, 'mentee_count': mentee_count, 'assigned_classes': assigned_classes})
    
    unassigned_batches = [b for b in target_class.batches if not b.mentor_assignment]
    
    if not unassigned_batches:
        flash("All batches in this class have an assigned mentor.", "info")
        return redirect(url_for('admin.manage_class', class_id=class_id))

    return render_template('admin/mentor_assignment.html',
                           target_class=target_class,
                           batches=unassigned_batches,
                           mentors_data=mentors_with_data)

@admin_bp.route('/class/<int:class_id>/upload_review', methods=['POST'])
@login_required
@role_required('admin')
def upload_and_review_students(class_id):
    Class.query.get_or_404(class_id)
    file = request.files.get('student_file')
    if not file or not file.filename.endswith(('.csv', '.xlsx')):
        flash("Please upload a valid CSV or Excel file.", "danger")
        return redirect(url_for('admin.manage_class', class_id=class_id))

    try:
        df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
        df.columns = [col.strip() for col in df.columns]
        required_columns = {'Reg_num', 'Name'}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            flash(f"File is missing required columns: {', '.join(missing_cols)}", "danger")
            return redirect(url_for('admin.manage_class', class_id=class_id))
    except Exception as e:
        flash(f"Error reading file: {e}", "danger")
        return redirect(url_for('admin.manage_class', class_id=class_id))

    df.dropna(how='all', inplace=True)
    df['Reg_num'] = df['Reg_num'].astype(str)
    df['Name'] = df['Name'].astype(str)
    
    existing_reg_nums_db = {str(item[0]) for item in MenteeProfile.query.with_entities(MenteeProfile.reg_num).all()}
    
    valid_students, invalid_rows, db_duplicates = [], [], []
    seen_reg_nums_in_file, seen_names_in_file = set(), set()

    for index, row in df.iterrows():
        errors = []
        reg_num = row.get('Reg_num', '').strip()
        name = row.get('Name', '').strip()

        if not reg_num: errors.append("Reg_num is missing.")
        if not name: errors.append("Name is missing.")
        if not reg_num.isdigit(): errors.append("Reg_num must be numeric.")
        if any(char.isdigit() for char in name): errors.append("Name cannot contain numbers.")

        if reg_num in seen_reg_nums_in_file: errors.append("Reg_num is duplicated within this file.")
        seen_reg_nums_in_file.add(reg_num)
        
        if name.lower() in seen_names_in_file: errors.append("Name is duplicated within this file.")
        seen_names_in_file.add(name.lower())

        student_data = {'Reg_num': reg_num, 'Name': name}
        
        if reg_num in existing_reg_nums_db:
            db_duplicates.append(student_data)
        elif errors:
            invalid_rows.append({'data': student_data, 'errors': errors})
        else:
            valid_students.append(student_data)
    
    session['valid_students_to_import'] = valid_students
    session['import_class_id'] = class_id
    
    return render_template('admin/confirm_import.html', 
                           valid_students=valid_students,
                           invalid_rows=invalid_rows,
                           db_duplicates=db_duplicates, 
                           class_id=class_id)

@admin_bp.route('/class/<int:class_id>/confirm_import', methods=['POST'])
@login_required
@role_required('admin')
def confirm_student_import(class_id):
    students_to_import = session.get('valid_students_to_import', [])
    import_class_id = session.get('import_class_id')

    if not students_to_import or import_class_id != class_id:
        flash("No valid student data to import or session expired. Please upload again.", "danger")
        return redirect(url_for('admin.manage_classes'))

    try:
        for student_data in students_to_import:
            reg_num_str = str(student_data.get('Reg_num'))
            user = User(
                name=student_data.get('Name'),
                role='mentee',
                must_change_password=True
            )
            user.set_password(reg_num_str)
            
            mentee_profile = MenteeProfile(
                user=user,
                reg_num=reg_num_str,
                class_id=class_id,
                profile_complete=False
            )
            db.session.add(user)
        
        db.session.commit()
        flash(f"{len(students_to_import)} new students have been successfully imported. They will be prompted to complete their profiles on first login.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during import: {e}. No students were added.", "danger")
    finally:
        session.pop('valid_students_to_import', None)
        session.pop('import_class_id', None)

    return redirect(url_for('admin.manage_class', class_id=class_id))

@admin_bp.route('/class/<int:class_id>/auto_batch', methods=['POST'])
@login_required
@role_required('admin')
def auto_batch_students(class_id):
    unbatched_mentees = list(MenteeProfile.query.filter_by(class_id=class_id, batch_id=None).order_by(MenteeProfile.reg_num).all())
    total_unbatched = len(unbatched_mentees)
    
    MIN_BATCH_SIZE = 20

    if total_unbatched < MIN_BATCH_SIZE:
        flash(f"At least {MIN_BATCH_SIZE} unbatched students are required to start auto-batching. Currently, there are only {total_unbatched}.", "warning")
        return redirect(url_for('admin.manage_class', class_id=class_id))

    batch_sizes = []
    remaining_students = total_unbatched
    
    num_full_batches = remaining_students // MIN_BATCH_SIZE
    remainder = remaining_students % MIN_BATCH_SIZE
    
    if num_full_batches <= 3:
        for _ in range(num_full_batches):
            batch_sizes.append(MIN_BATCH_SIZE)
        if remainder > 0:
            if batch_sizes:
                batch_sizes[-1] += remainder
            else:
                 batch_sizes.append(remainder)
    else: # num_full_batches > 3
        batch_sizes = [MIN_BATCH_SIZE] * 3
        remaining_after_3 = total_unbatched - 60
        
        if remaining_after_3 >= 10:
            batch_sizes.append(remaining_after_3)
        else:
            for i in range(remaining_after_3):
                batch_sizes[i % 3] += 1

    try:
        latest_batch = Batch.query.filter_by(class_id=class_id).order_by(Batch.name.desc()).first()
        start_num = 1
        if latest_batch and latest_batch.name.startswith('B') and latest_batch.name[1:].isdigit():
            start_num = int(latest_batch.name[1:]) + 1

        mentee_idx = 0
        for i, size in enumerate(batch_sizes):
            batch_name = f"B{start_num + i}"
            new_batch = Batch(name=batch_name, class_id=class_id)
            db.session.add(new_batch)
            
            mentees_for_this_batch = unbatched_mentees[mentee_idx : mentee_idx + size]
            for mentee in mentees_for_this_batch:
                mentee.batch = new_batch
            mentee_idx += size

        db.session.commit()
        flash(f"Successfully created {len(batch_sizes)} new batches for {total_unbatched} students.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during batch creation: {e}", "danger")

    return redirect(url_for('admin.manage_class', class_id=class_id))

@admin_bp.route('/class/<int:class_id>/manual_assignment', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manual_batch_assignment(class_id):
    target_class = Class.query.get_or_404(class_id)
    if request.method == 'POST':
        selected_batch_id = request.form.get('batch_id')
        student_ids = request.form.getlist('student_ids')
        
        if not selected_batch_id or not student_ids:
            flash("You must select a batch and at least one student.", "danger")
            return redirect(url_for('admin.manual_batch_assignment', class_id=class_id))
        
        mentees_to_assign = MenteeProfile.query.filter(MenteeProfile.user_id.in_(student_ids)).all()
        for mentee in mentees_to_assign:
            mentee.batch_id = selected_batch_id
        
        db.session.commit()
        flash(f"Successfully assigned {len(mentees_to_assign)} students to the selected batch.", "success")
        return redirect(url_for('admin.manage_class', class_id=class_id))
    
    unbatched_students = MenteeProfile.query.filter_by(class_id=class_id, batch_id=None).all()
    if not unbatched_students:
        flash("No students are available for manual assignment.", "info")
        return redirect(url_for('admin.manage_class', class_id=class_id))
        
    existing_batches = Batch.query.filter_by(class_id=class_id).order_by(Batch.name).all()
    return render_template('admin/manual_batch_assignment.html',
                           target_class=target_class,
                           students=unbatched_students,
                           batches=existing_batches)

@admin_bp.route('/assignment/<int:assignment_id>/edit', methods=['GET'])
@login_required
@role_required('admin')
def edit_assignment(assignment_id):
    assignment = MentorAssignment.query.get_or_404(assignment_id)
    now = datetime.now(timezone.utc)
    upcoming_sessions = Session.query.filter(
        Session.mentor_assignment_id == assignment_id,
        Session.start_time > now
    ).order_by(Session.start_time).all()
    
    available_mentors = User.query.filter(User.role == 'mentor', User.is_active == True).order_by(User.name).all()
    
    return render_template('admin/edit_assignment.html',
                           assignment=assignment,
                           upcoming_sessions=upcoming_sessions,
                           mentors=available_mentors)

@admin_bp.route('/assignment/<int:assignment_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_assignment(assignment_id):
    assignment = MentorAssignment.query.get_or_404(assignment_id)
    class_id = assignment.batch.class_id
    action = request.form.get('action')
    now = datetime.now(timezone.utc)

    try:
        upcoming_sessions_to_delete = Session.query.filter(
            Session.mentor_assignment_id == assignment_id,
            Session.start_time > now
        )
        
        if action == 'unassign':
            upcoming_sessions_to_delete.delete(synchronize_session=False)
            db.session.delete(assignment)
            flash(f"Mentor for batch {assignment.batch.name} has been unassigned and future sessions deleted.", "success")

        elif action in ['reschedule', 'reassign']:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            day_of_week = int(request.form.get('day_of_week'))
            session_time = datetime.strptime(request.form.get('time'), '%H:%M').time()
            num_weeks = int(request.form.get('num_weeks'))
            
            mentor_id_for_check = int(request.form.get('mentor_id')) if action == 'reassign' else assignment.mentor_id

            days_ahead = (day_of_week - start_date.weekday() + 7) % 7
            current_date = start_date + timedelta(days=days_ahead)
            
            sessions_to_create_dates = []
            while len(sessions_to_create_dates) < num_weeks:
                if not is_third_saturday(current_date):
                    sessions_to_create_dates.append(current_date)
                current_date += timedelta(weeks=1)
            
            session_datetimes = [LOCAL_TIMEZONE.localize(datetime.combine(d, session_time)).astimezone(timezone.utc) for d in sessions_to_create_dates]

            collision_message = check_for_collision(mentor_id_for_check, session_datetimes, existing_assignment_id=assignment_id)
            if collision_message:
                flash(collision_message, "danger")
                return redirect(url_for('admin.edit_assignment', assignment_id=assignment_id))

            upcoming_sessions_to_delete.delete(synchronize_session=False)

            if action == 'reassign':
                db.session.delete(assignment)
                new_assignment = MentorAssignment(mentor_id=mentor_id_for_check, batch_id=assignment.batch_id, is_active=True)
                db.session.add(new_assignment)
                assignment_to_update = new_assignment
            else:
                assignment_to_update = assignment

            for i, dt in enumerate(session_datetimes):
                new_session = Session(session_number=i + 1, start_time=dt, status='Upcoming')
                assignment_to_update.sessions.append(new_session)
            
            flash("Assignment has been successfully updated.", "success")
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {e}", "danger")
        return redirect(url_for('admin.edit_assignment', assignment_id=assignment_id))

    return redirect(url_for('admin.manage_class', class_id=class_id))

@admin_bp.route('/completed_sessions')
@login_required
@role_required('admin')
def completed_sessions():
    sessions = Session.query.filter(
        Session.status.in_(['Completed', 'Missed'])
    ).order_by(Session.start_time.desc()).all()
    
    return render_template('completed_sessions.html', sessions=sessions)

@admin_bp.route('/session/<int:session_id>/details')
@login_required
@role_required('admin')
def session_details(session_id):
    session = Session.query.get_or_404(session_id)

    models_to_check = {
        'Placement Information': PlacementInformation, 'Research Record': ResearchRecord, 
        'Academic Mark Details': AcademicSemesterMarkDetails, 'Mentor Meeting Details': MentorMeetingDetails,
        'Awards and Achievements': AwardsAndAchievements, 'Co-Curricular Activity': CocurricularActivityRecord, 
        'Extra-Curricular Activity': ExtracurricularActivityRecord, 'Internship Information': InternshipInformation,
        'Honors Minor Marks Details': HonorsMinorMarksDetails
    }
    
    all_mentees_in_session = session.assignment.batch.mentees.join(User).order_by(User.name).all() 
    all_data = {}

    for mentee_profile in all_mentees_in_session:
        mentee_user = mentee_profile.user
        mentee_records = {}
        
        for name, model in models_to_check.items():
            records = model.query.filter_by(session_id=session.id, mentee_id=mentee_user.id).all()
            if records:
                mentee_records[name] = [model_to_dict(r) for r in records]

        approved_leave = LeaveRequest.query.filter_by(session_id=session.id, mentee_id=mentee_user.id, status='Approved').first()
        marked_absent = AttendanceRecord.query.filter_by(session_id=session.id, mentee_id=mentee_user.id, status='Absent').first()
        status_info = None
        if approved_leave:
            status_info = { "status": "Leave Approved", "details": f"Requested on {timestamp_to_local(approved_leave.requested_at, 'date_only')}, Approved on {timestamp_to_local(approved_leave.actioned_at, 'date_only')}"}
        elif marked_absent:
            status_info = { "status": "Marked Absent", "details": f"Marked as absent by mentor."}
        else:
            status_info = { "status": "Present", "details": ""}
            
        all_data[mentee_user.id] = {'name': mentee_user.name, 'records': mentee_records, 'attendance': status_info}

    return render_template('session_details.html', session=session, all_data=all_data)