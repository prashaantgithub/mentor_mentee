from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from ..utils import role_required, timestamp_to_local
from .. import db
from ..models import (User, Class, Batch, MentorAssignment, Session, LeaveRequest, Notification,
                     MenteeProfile, MentorProfile, AttendanceRecord, PlacementInformation, ResearchRecord, 
                     AcademicSemesterMarkDetails, MentorMeetingDetails, AwardsAndAchievements, 
                     CocurricularActivityRecord, ExtracurricularActivityRecord, InternshipInformation,
                     HonorsMinorMarksDetails)
from datetime import datetime, time, timedelta, timezone, date
import pytz
from sqlalchemy import or_

api_bp = Blueprint('api', __name__, url_prefix='/api')

LOCAL_TIMEZONE = pytz.timezone('Asia/Kolkata')

def is_third_saturday(d):
    return d.weekday() == 5 and 15 <= d.day <= 21

def check_for_collision(mentor_id, session_datetimes):
    existing_sessions = Session.query.join(MentorAssignment).filter(
        MentorAssignment.mentor_id == mentor_id,
        Session.start_time.in_(session_datetimes)
    ).first()

    if existing_sessions:
        colliding_batch = existing_sessions.assignment.batch
        colliding_class = colliding_batch.class_model
        return f"Schedule conflict detected! Mentor is already assigned to {colliding_class.name} - {colliding_batch.name} at that time."
    return None

def validate_record_data(form_type, data):
    required_fields = {
        'placement_information': ['company_name', 'interview_date', 'rounds_attended', 'internship_provided', 'interview_status'],
        'research_record': ['title', 'publication_name', 'publication_date', 'publication_type', 'publication_status'],
        'mentor_meeting_details': ['points_discussed', 'remarks_given'],
        'awards_achievements': ['award_achievement_name', 'conducted_by', 'date'],
        'cocurricular_activity': ['activity_name', 'activity_type', 'conducted_by', 'date'],
        'extracurricular_activity': ['activity_name', 'activity_type', 'conducted_by', 'date'],
        'internship_information': ['company_name', 'duration_from', 'duration_to', 'sem', 'technology_domain', 'internship_status'],
    }
    
    if form_type in required_fields:
        for field in required_fields[form_type]:
            if not data.get(field):
                return f"Field '{field}' is required and cannot be empty."

    if form_type == 'internship_information':
        from_date_str = data.get('duration_from')
        to_date_str = data.get('duration_to')
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            if from_date > to_date:
                return "Duration From date cannot be after Duration To date."
        except (ValueError, TypeError):
            if from_date_str or to_date_str:
                return "Invalid date format for duration fields. Please use YYYY-MM-DD."
            
    return None

@api_bp.route('/admin/filter_users', methods=['GET'])
@login_required
@role_required('admin')
def filter_users():
    role = request.args.get('role', 'mentee')
    department = request.args.get('department')
    class_id = request.args.get('class_id')
    batch_id = request.args.get('batch_id')
    search_term = request.args.get('search_term')
    sort_by = request.args.get('sort_by', 'name_asc')

    query = User.query.filter_by(role=role, is_active=True)

    if role == 'mentee':
        query = query.join(MenteeProfile)
        if class_id:
            query = query.filter(MenteeProfile.class_id == class_id)
        if batch_id:
            query = query.filter(MenteeProfile.batch_id == batch_id)
        if search_term:
            search_filter = or_(
                User.name.ilike(f'%{search_term}%'),
                MenteeProfile.reg_num.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
    
    elif role == 'mentor':
        if department:
            mentor_ids_in_dept = db.session.query(MentorAssignment.mentor_id).join(Batch).join(MenteeProfile).filter(MenteeProfile.department == department).distinct()
            query = query.filter(User.id.in_(mentor_ids_in_dept))

        if search_term:
            query = query.filter(User.name.ilike(f'%{search_term}%'))

    if sort_by == 'name_asc':
        query = query.order_by(User.name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(User.name.desc())
    elif sort_by == 'reg_num_asc' and role == 'mentee':
        query = query.order_by(MenteeProfile.reg_num.asc())
    elif sort_by == 'reg_num_desc' and role == 'mentee':
        query = query.order_by(MenteeProfile.reg_num.desc())
    
    users = query.all()

    users_data = []
    for user in users:
        data = {'id': user.id, 'name': user.name, 'email': user.email}
        if role == 'mentee' and user.mentee_profile:
            data['reg_num'] = user.mentee_profile.reg_num
            data['class'] = user.mentee_profile.assigned_class.name if user.mentee_profile.assigned_class else 'N/A'
            data['batch'] = user.mentee_profile.batch.name if user.mentee_profile.batch else 'N/A'
        users_data.append(data)

    return jsonify(success=True, users=users_data)

@api_bp.route('/admin/class/<int:class_id>/batches', methods=['GET'])
@login_required
@role_required('admin')
def get_class_batches(class_id):
    target_class = Class.query.get_or_404(class_id)
    batches = target_class.batches.order_by(Batch.name).all()
    batches_data = [{'id': batch.id, 'name': batch.name} for batch in batches]
    return jsonify(success=True, batches=batches_data)


@api_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not current_user.check_password(current_password):
        return jsonify(success=False, message="Current password is not correct."), 400
    
    if not new_password or len(new_password) < 6:
        return jsonify(success=False, message="New password must be at least 6 characters long."), 400
        
    if new_password != confirm_password:
        return jsonify(success=False, message="New passwords do not match."), 400
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify(success=True, message="Password updated successfully.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"An error occurred: {e}"), 500

@api_bp.route('/admin/unassigned_batches', methods=['GET'])
@login_required
@role_required('admin')
def get_unassigned_batches():
    assigned_batch_ids = db.session.query(MentorAssignment.batch_id).filter_by(is_active=True)
    
    unassigned_batches_query = db.session.query(
        Batch,
        Class.name.label('class_name')
    ).join(Class, Batch.class_id == Class.id).filter(
        Batch.id.notin_(assigned_batch_ids),
        Class.is_archived == False
    ).order_by(Class.name, Batch.name).all()
    
    batches_list = [{'id': batch.id, 'name': f"{class_name} - {batch.name}", 'student_count': batch.mentees.count()} for batch, class_name in unassigned_batches_query]
    return jsonify(success=True, batches=batches_list)

@api_bp.route('/admin/mentors', methods=['GET'])
@login_required
@role_required('admin')
def get_mentors():
    mentors = User.query.filter_by(role='mentor', is_active=True).order_by(User.name).all()
    mentors_list = [{'id': m.id, 'name': m.name} for m in mentors]
    return jsonify(success=True, mentors=mentors_list)

@api_bp.route('/admin/assign_and_schedule', methods=['POST'])
@login_required
@role_required('admin')
def assign_and_schedule():
    data = request.get_json()
    mentor_id = data.get('mentor_id')
    batch_ids = data.get('batch_ids')
    schedule_data = data.get('schedule')

    if not all([mentor_id, batch_ids, schedule_data]):
        return jsonify(success=False, message="Missing mentor, batches, or schedule data."), 400

    mentor = User.query.filter_by(id=mentor_id, role='mentor').first()
    if not mentor:
        return jsonify(success=False, message="Invalid mentor selected."), 404

    try:
        start_date = datetime.strptime(schedule_data['start_date'], '%Y-%m-%d').date()
        session_day_of_week = int(schedule_data['day_of_week'])
        session_time = datetime.strptime(schedule_data['time'], '%H:%M').time()
        num_weeks = int(schedule_data['num_weeks'])

        days_ahead = (session_day_of_week - start_date.weekday() + 7) % 7
        current_date = start_date + timedelta(days=days_ahead)
        
        sessions_to_create_dates = []
        while len(sessions_to_create_dates) < num_weeks:
            if not is_third_saturday(current_date):
                sessions_to_create_dates.append(current_date)
            current_date += timedelta(weeks=1)
        
        session_datetimes_utc = [LOCAL_TIMEZONE.localize(datetime.combine(d, session_time)).astimezone(timezone.utc) for d in sessions_to_create_dates]

        collision_message = check_for_collision(mentor_id, session_datetimes_utc)
        if collision_message:
            return jsonify(success=False, collision=True, message=collision_message), 409

        for batch_id in batch_ids:
            assignment = MentorAssignment(mentor_id=mentor_id, batch_id=batch_id, original_mentor_id=mentor_id, is_active=True)
            for i, dt in enumerate(session_datetimes_utc):
                new_session = Session(session_number=i + 1, start_time=dt, status='Upcoming')
                assignment.sessions.append(new_session)
            db.session.add(assignment)
        
        db.session.commit()
        return jsonify(success=True, message="Batches assigned and sessions scheduled successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"Error during assignment: {e}") 
        return jsonify(success=False, message=f"An error occurred during assignment. Please check the data and try again."), 500

@api_bp.route('/admin/batch/<int:batch_id>/students', methods=['GET'])
@login_required
@role_required('admin')
def get_batch_students(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    students = MenteeProfile.query.filter_by(batch_id=batch.id).join(User).order_by(User.name).all()
    
    student_list = [{'name': student.user.name, 'reg_num': student.reg_num} for student in students]
    return jsonify(success=True, students=student_list, batch_name=batch.name)

@api_bp.route('/mentor/session/add_record', methods=['POST'])
@login_required
@role_required('mentor')
def add_session_record():
    data = request.get_json()
    form_type = data.get('form_type')
    
    validation_error = validate_record_data(form_type, data)
    if validation_error:
        return jsonify(success=False, message=validation_error), 400

    mentee_id = data.pop('mentee_id', None)
    session_id = data.pop('session_id', None)
    _form_type_unused = data.pop('form_type', None)

    if not all([mentee_id, session_id, form_type]):
        return jsonify(success=False, message="Missing essential record identification (mentee, session, form type)."), 400

    form_map = {
        'placement_information': PlacementInformation, 'research_record': ResearchRecord,
        'mentor_meeting_details': MentorMeetingDetails, 'awards_achievements': AwardsAndAchievements, 
        'cocurricular_activity': CocurricularActivityRecord, 'extracurricular_activity': ExtracurricularActivityRecord, 
        'internship_information': InternshipInformation
    }

    if form_type not in form_map:
        return jsonify(success=False, message="Invalid form type specified."), 400
    
    ModelClass = form_map[form_type]
    
    session_obj = Session.query.get_or_404(session_id)
    if session_obj.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403

    try:
        if 'internship_provided' in data:
            data['internship_provided'] = data['internship_provided'] == 'true'
        
        for key, value in list(data.items()):
            if value == '': data[key] = None
        
        for key, value in list(data.items()):
            if value == '': data[key] = None

        existing_record = ModelClass.query.filter_by(session_id=session_id, mentee_id=mentee_id).first()
        
        if existing_record:
            for key, value in data.items():
                if hasattr(existing_record, key) and key != 'id':
                    setattr(existing_record, key, value)
        else:
            new_record_data = data.copy()
            new_record_data['mentee_id'] = mentee_id
            new_record_data['session_id'] = session_id
            new_record = ModelClass(**new_record_data)
            db.session.add(new_record)
        
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        print(f"Error saving record: {e}")
        return jsonify(success=False, message=f"An error occurred while saving the record: {str(e)}"), 500

@api_bp.route('/mentor/session/add_multi_record', methods=['POST'])
@login_required
@role_required('mentor')
def add_multi_session_record():
    data = request.get_json()
    form_type = data.get('form_type')
    records_data = data.get('records', [])
    
    ModelClass = None
    if form_type == 'academic_mark_details':
        ModelClass = AcademicSemesterMarkDetails
    elif form_type == 'honors_minor_marks':
        ModelClass = HonorsMinorMarksDetails
    else:
        return jsonify(success=False, message="Invalid form type for multi-record."), 400

    session_obj = Session.query.get_or_404(data.get('session_id'))
    if session_obj.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403

    try:
        ModelClass.query.filter_by(session_id=data['session_id'], mentee_id=data['mentee_id']).delete()
        
        for record_data in records_data:
            record_data['mentee_id'] = data['mentee_id']
            record_data['session_id'] = data['session_id']
            
            if form_type == 'honors_minor_marks':
                record_data['semester'] = data.get('course_type', 'N/A')
            
            if 'course_acceleration_deceleration' in record_data and record_data['course_acceleration_deceleration'] == True:
                 record_data['course_acceleration_deceleration'] = 'Acceleration/De-Acceleration'
            else:
                record_data.pop('course_acceleration_deceleration', None)

            for key, value in list(record_data.items()):
                if value == '':
                    record_data[key] = None

            new_record = ModelClass(**record_data)
            db.session.add(new_record)
        
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        print(f"Error saving multi-record: {e}")
        return jsonify(success=False, message="An error occurred while saving records."), 500

@api_bp.route('/mentor/session/attendance', methods=['POST'])
@login_required
@role_required('mentor')
def update_attendance():
    data = request.get_json()
    session_id = data.get('session_id')
    mentee_id = data.get('mentee_id')
    status = data.get('status')

    session_obj = Session.query.get_or_404(session_id)
    if session_obj.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403

    try:
        if status == "Absent":
            existing_record = AttendanceRecord.query.filter_by(session_id=session_id, mentee_id=mentee_id).first()
            if not existing_record:
                record = AttendanceRecord(session_id=session_id, mentee_id=mentee_id, status='Absent')
                db.session.add(record)
            else:
                existing_record.status = 'Absent'
        elif status == "Present":
            AttendanceRecord.query.filter_by(session_id=session_id, mentee_id=mentee_id).delete()
        else:
            return jsonify(success=False, message="Invalid status"), 400
            
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        print(f"Error updating attendance: {e}")
        return jsonify(success=False, message="An error occurred while updating attendance."), 500

@api_bp.route('/mentor/session/<int:session_id>/start', methods=['POST'])
@login_required
@role_required('mentor')
def start_session(session_id):
    session = Session.query.get_or_404(session_id)
    if session.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403
    
    if not session.actual_start_time:
        session.actual_start_time = datetime.now(timezone.utc)
        session.status = "In Progress"
        db.session.commit()
    
    return jsonify(success=True)

@api_bp.route('/mentor/session/end', methods=['POST'])
@login_required
@role_required('mentor')
def end_session():
    data = request.get_json()
    session_id = data.get('session_id')
    session_obj = Session.query.get(session_id)
    if session_obj and session_obj.assignment.mentor_id == current_user.id:
        session_obj.status = 'Completed'
        session_obj.actual_end_time = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, message="Session not found or unauthorized."), 404

@api_bp.route('/mentor/session/get_records', methods=['GET'])
@login_required
@role_required('mentor')
def get_session_records():
    session_id = request.args.get('session_id')
    mentee_id = request.args.get('mentee_id')
    records = {}
    
    def model_to_dict(model_instance):
        d = {}
        for column in model_instance.__table__.columns:
            val = getattr(model_instance, column.name)
            d[column.name] = val.isoformat() if isinstance(val, (datetime, date)) else val
        return d
        
    models_to_check = { 
        'placement_information': PlacementInformation, 'research_record': ResearchRecord, 
        'academic_mark_details': AcademicSemesterMarkDetails, 'awards_achievements': AwardsAndAchievements, 
        'cocurricular_activity': CocurricularActivityRecord, 'extracurricular_activity': ExtracurricularActivityRecord,
        'internship_information': InternshipInformation, 'mentor_meeting_details': MentorMeetingDetails,
        'honors_minor_marks': HonorsMinorMarksDetails 
    }

    for name, model in models_to_check.items():
        if name == 'mentor_meeting_details':
            continue 
            
        record_results = model.query.filter_by(session_id=session_id, mentee_id=mentee_id).all()
        if record_results: 
            records[name] = [model_to_dict(r) for r in record_results]

    return jsonify(success=True, records=records)

@api_bp.route('/mentor/session/get_attendance', methods=['GET'])
@login_required
@role_required('mentor')
def get_attendance():
    session_id = request.args.get('session_id')
    mentee_id = request.args.get('mentee_id')

    session_obj = Session.query.get_or_404(session_id)
    if session_obj.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403

    has_approved_leave = LeaveRequest.query.filter_by(
        session_id=session_id, mentee_id=mentee_id, status='Approved'
    ).first()

    if has_approved_leave:
        return jsonify(success=True, is_absent=True, has_leave=True)
    
    is_absent = AttendanceRecord.query.filter_by(
        session_id=session_id, mentee_id=mentee_id, status='Absent'
    ).first()
    
    return jsonify(success=True, is_absent=bool(is_absent), has_leave=False)


@api_bp.route('/mentee/session/<int:session_id>/request_leave', methods=['POST'])
@login_required
def request_leave(session_id):
    if current_user.role != 'mentee':
        return jsonify(success=False, message="Unauthorized"), 403
    
    reason = request.json.get('reason')
    if not reason:
        return jsonify(success=False, message="A reason for the leave is required."), 400

    session = Session.query.get_or_404(session_id)
    mentor_id = session.assignment.mentor_id
    
    existing_request = LeaveRequest.query.filter_by(session_id=session_id, mentee_id=current_user.id).first()
    if existing_request:
        return jsonify(success=False, message="You have already submitted a request for this session."), 409

    try:
        new_request = LeaveRequest(session_id=session_id, mentee_id=current_user.id, reason=reason)
        notification = Notification(
            user_id=mentor_id,
            message=f"{current_user.name} has requested leave for the session on {session.start_time.strftime('%d-%b-%Y')}.",
            link=url_for('mentor.leave_requests')
        )
        db.session.add(new_request)
        db.session.add(notification)
        db.session.commit()
        return jsonify(success=True, message="Leave request submitted successfully.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"An error occurred: {e}"), 500

@api_bp.route('/mentor/request/<int:request_id>/action', methods=['POST'])
@login_required
@role_required('mentor')
def action_leave_request(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    session = leave_request.session
    action = request.json.get('action')

    if session.assignment.mentor_id != current_user.id:
        return jsonify(success=False, message="Unauthorized"), 403

    if action not in ['approve', 'decline']:
        return jsonify(success=False, message="Invalid action."), 400

    try:
        leave_request.status = 'Approved' if action == 'approve' else 'Declined'
        leave_request.actioned_at = datetime.now(timezone.utc)
        
        notification = Notification(
            user_id=leave_request.mentee_id,
            message=f"Your leave request for the session on {session.start_time.strftime('%d-%b-%Y')} has been {leave_request.status}.",
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify(success=True, message=f"Request has been {leave_request.status}.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"An error occurred: {e}"), 500

@api_bp.route('/session/<int:session_id>/details', methods=['GET'])
@login_required
def get_session_details(session_id):
    session = Session.query.get_or_404(session_id)
    
    is_admin = current_user.role == 'admin'
    is_assigned_mentor = current_user.role == 'mentor' and session.assignment.mentor_id == current_user.id
    
    is_assigned_mentee = False
    if current_user.role == 'mentee' and hasattr(current_user, 'mentee_profile') and current_user.mentee_profile:
        is_assigned_mentee = current_user.mentee_profile.batch_id == session.assignment.batch_id

    if not (is_admin or is_assigned_mentor or is_assigned_mentee):
        return jsonify(success=False, message="Unauthorized"), 403

    mentor_user = session.assignment.mentor
    if not mentor_user:
        return jsonify(success=False, message="Mentor not found for this session."), 404
        
    mentor_profile = mentor_user.mentor_profile

    cabin_details_parts = []
    if mentor_profile:
        if mentor_profile.cabin_block: cabin_details_parts.append(f"Block: {mentor_profile.cabin_block}")
        if mentor_profile.cabin_floor: cabin_details_parts.append(f"{mentor_profile.cabin_floor} Floor")
        if mentor_profile.cabin_number: cabin_details_parts.append(f"Cabin No: {mentor_profile.cabin_number}")
    
    cabin_details_str = ", ".join(cabin_details_parts) if cabin_details_parts else "Not available"
    formatted_time = timestamp_to_local(session.start_time, format_type='full')

    details = {
        'meeting_time': formatted_time,
        'mentor_name': mentor_user.name,
        'cabin_details': cabin_details_str,
    }
    
    return jsonify(success=True, details=details)