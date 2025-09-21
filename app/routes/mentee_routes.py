from flask import Blueprint, render_template, abort, redirect, url_for, request, flash, Response, current_app
from flask_login import login_required, current_user
from ..utils.__init__ import role_required, timestamp_to_local
from ..models import (User, MenteeProfile, Session, MentorAssignment, LeaveRequest, PlacementInformation, ResearchRecord, 
                     AcademicSemesterMarkDetails, MentorMeetingDetails, AwardsAndAchievements, 
                     CocurricularActivityRecord, ExtracurricularActivityRecord, InternshipInformation,
                     HonorsMinorMarksDetails, AttendanceRecord, Class, Batch)
from datetime import datetime, timezone, date, timedelta
from .. import db
from ..utils.report_generator import generate_mentee_full_report

mentee_bp = Blueprint('mentee', __name__, url_prefix='/mentee')

def model_to_dict(model_instance):
    d = {}
    for column in model_instance.__table__.columns:
        val = getattr(model_instance, column.name)
        if isinstance(val, (datetime, date)):
            d[column.name] = val.isoformat()
        else:
            d[column.name] = val
    return d

@mentee_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
@role_required('mentee')
def dashboard():
    mentee_profile = current_user.mentee_profile
    if not mentee_profile:
        abort(404)
        
    if request.method == 'POST':
        try:
            email = request.form.get('email').strip().lower()
            valid_domains = ['@btech.christuniversity.in', '@mtech.christuniversity.in']
            
            if not any(email.endswith(domain) for domain in valid_domains):
                flash('Invalid email domain. Please use your official university email (...@btech.christuniversity.in or ...@mtech.christuniversity.in).', 'danger')
                return redirect(url_for('mentee.dashboard'))

            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                flash('This email address is already in use. Please choose another.', 'danger')
                return redirect(url_for('mentee.dashboard'))
            
            current_user.email = email
            
            mentee_profile.admission_number = request.form.get('admission_number')
            mentee_profile.year_of_joining = request.form.get('year_of_joining')
            mentee_profile.programme = request.form.get('programme')
            mentee_profile.department = request.form.get('department')
            mentee_profile.residential_phone = request.form.get('residential_phone')
            mentee_profile.personal_cell = request.form.get('personal_cell')
            
            dob_str = request.form.get('dob')
            if dob_str:
                mentee_profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
            mentee_profile.age = request.form.get('age')
            mentee_profile.blood_group = request.form.get('blood_group')
            
            mentee_profile.father_name = request.form.get('father_name')
            mentee_profile.father_education = request.form.get('father_education')
            mentee_profile.father_occupation = request.form.get('father_occupation')
            mentee_profile.father_phone = request.form.get('father_phone')
            mentee_profile.father_email = request.form.get('father_email')

            mentee_profile.mother_name = request.form.get('mother_name')
            mentee_profile.mother_education = request.form.get('mother_education')
            mentee_profile.mother_occupation = request.form.get('mother_occupation')
            mentee_profile.mother_phone = request.form.get('mother_phone')
            mentee_profile.mother_email = request.form.get('mother_email')
            
            mentee_profile.family_income = request.form.get('family_income')
            mentee_profile.siblings = request.form.get('siblings')
            mentee_profile.local_residence_type = request.form.get('local_residence_type')
            mentee_profile.guardian_name = request.form.get('guardian_name')
            mentee_profile.guardian_relationship = request.form.get('guardian_relationship')
            mentee_profile.hostel_location = request.form.get('hostel_location')
            mentee_profile.hostel_name = request.form.get('hostel_name')
            mentee_profile.pg_owner_name = request.form.get('pg_owner_name')
            mentee_profile.pg_owner_mobile = request.form.get('pg_owner_mobile')
            mentee_profile.residence_address = request.form.get('residence_address')
            
            mentee_profile.profile_complete = True
            
            db.session.commit()
            flash('Profile updated successfully! Welcome to your dashboard.', 'success')
            return redirect(url_for('mentee.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating your profile: {e}', 'danger')

    force_profile_update = not mentee_profile.profile_complete
    
    if force_profile_update:
        return render_template('mentee/dashboard.html', 
                               mentee_profile=mentee_profile, 
                               force_profile_update=True)

    sessions_with_status = []
    if mentee_profile.batch_id:
        now_utc = datetime.now(timezone.utc)
        upcoming_sessions = db.session.query(Session).join(
            MentorAssignment, Session.mentor_assignment_id == MentorAssignment.id
        ).filter(
            MentorAssignment.batch_id == mentee_profile.batch_id,
            MentorAssignment.is_active == True,
            Session.status.in_(['Upcoming', 'In Progress']),
            Session.start_time >= now_utc
        ).order_by(Session.start_time.asc()).all()

        if upcoming_sessions:
            session_ids = [s.id for s in upcoming_sessions]
            leave_requests = LeaveRequest.query.filter(
                LeaveRequest.session_id.in_(session_ids),
                LeaveRequest.mentee_id == current_user.id
            ).all()
            
            requests_map = {req.session_id: req.status for req in leave_requests}
            for session in upcoming_sessions:
                sessions_with_status.append({'session': session, 'leave_status': requests_map.get(session.id)})

    return render_template('mentee/dashboard.html', 
                           mentee_profile=mentee_profile, 
                           sessions_with_status=sessions_with_status, 
                           force_profile_update=False)

@mentee_bp.route('/completed_sessions')
@login_required
@role_required('mentee')
def completed_sessions():
    mentee_profile = current_user.mentee_profile
    sessions = []
    if mentee_profile and mentee_profile.batch_id:
        assignment = MentorAssignment.query.filter_by(batch_id=mentee_profile.batch_id, is_active=True).first()
        if assignment:
            sessions = Session.query.filter(
                Session.mentor_assignment_id == assignment.id,
                Session.status.in_(['Completed', 'Missed'])
            ).order_by(Session.start_time.desc()).all()
            
    return render_template('completed_sessions.html', sessions=sessions)

@mentee_bp.route('/session/<int:session_id>/details')
@login_required
@role_required('mentee')
def session_details(session_id):
    session = Session.query.get_or_404(session_id)
    mentee_profile = current_user.mentee_profile

    if not mentee_profile or session.assignment.batch_id != mentee_profile.batch_id:
        abort(403)

    models_to_check = {
        'Placement Information': PlacementInformation, 'Research Record': ResearchRecord, 
        'Academic Mark Details': AcademicSemesterMarkDetails, 'Mentor Meeting Details': MentorMeetingDetails,
        'Awards and Achievements': AwardsAndAchievements, 'Co-Curricular Activity': CocurricularActivityRecord, 
        'Extra-Curricular Activity': ExtracurricularActivityRecord, 'Internship Information': InternshipInformation,
        'Honors Minor Marks Details': HonorsMinorMarksDetails
    }
    
    mentee_records = {}
    for name, model in models_to_check.items():
        records = model.query.filter_by(session_id=session.id, mentee_id=current_user.id).all()
        if records:
            mentee_records[name] = [model_to_dict(r) for r in records]

    approved_leave = LeaveRequest.query.filter_by(session_id=session.id, mentee_id=current_user.id, status='Approved').first()
    marked_absent = AttendanceRecord.query.filter_by(session_id=session.id, mentee_id=current_user.id, status='Absent').first()
    status_info = None
    if approved_leave:
        status_info = { "status": "Leave Approved", "details": f"Requested on {timestamp_to_local(approved_leave.requested_at, 'date_only')}, Approved on {timestamp_to_local(approved_leave.actioned_at, 'date_only')}"}
    elif marked_absent:
        status_info = { "status": "Marked Absent", "details": f"Marked as absent by mentor."}
    else:
        status_info = { "status": "Present", "details": ""}
            
    return render_template('mentee/session_details.html', 
                           session=session, 
                           mentee_records=mentee_records,
                           attendance_status=status_info)

@mentee_bp.route('/download_full_report')
@login_required
@role_required('mentee')
def download_mentee_full_report():
    mentee_user = current_user
    mentee_profile = mentee_user.mentee_profile

    if not mentee_profile:
        abort(404)

    pdf_bytes, filename = generate_mentee_full_report(mentee_user.id) 

    if pdf_bytes is None:
        flash("Could not generate report.", "danger")
        return redirect(url_for('mentee.dashboard'))

    response = Response(
        pdf_bytes,
        mimetype='application/pdf'
    )
    response.headers['Content-Disposition'] = f'attachment;filename={filename}' 
    return response