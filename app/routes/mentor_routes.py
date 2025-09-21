from flask import Blueprint, render_template, abort, redirect, url_for, flash, Response, current_app
from flask_login import login_required, current_user
from ..utils.__init__ import role_required, timestamp_to_local
from ..models import (User, Batch, MenteeProfile, MentorAssignment, Session, Class, LeaveRequest,
                     AttendanceRecord, AcademicSemesterMarkDetails, PlacementInformation, ResearchRecord, 
                     HonorsMinorMarksDetails, MentorMeetingDetails, AwardsAndAchievements, 
                     CocurricularActivityRecord, ExtracurricularActivityRecord, InternshipInformation)
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import distinct, or_
from .. import db
from ..utils.report_generator import generate_mentee_full_report

mentor_bp = Blueprint('mentor', __name__, url_prefix='/mentor')

def model_to_dict(model_instance):
    d = {}
    for column in model_instance.__table__.columns:
        val = getattr(model_instance, column.name)
        if isinstance(val, (datetime, date)):
            d[column.name] = val.isoformat()
        else:
            d[column.name] = val
    return d

@mentor_bp.route('/dashboard')
@login_required
@role_required('mentor')
def dashboard():
    return redirect(url_for('mentor.sessions'))

@mentor_bp.route('/sessions')
@login_required
@role_required('mentor')
def sessions():
    now = datetime.now(timezone.utc)
    session_duration = timedelta(hours=1)
    
    base_query = Session.query.join(MentorAssignment).filter(
        MentorAssignment.mentor_id == current_user.id,
        MentorAssignment.is_active == True
    )

    live_sessions = base_query.filter(
        Session.start_time <= now,
        Session.start_time > (now - session_duration),
        Session.status.in_(['Upcoming', 'In Progress'])
    ).order_by(Session.start_time.asc()).all()

    upcoming_sessions = base_query.filter(
        Session.start_time > now,
        Session.status == 'Upcoming'
    ).order_by(Session.start_time.asc()).all()
    
    filter_data_query = db.session.query(
        Class.name.label('class_name'),
        Batch.name.label('batch_name')
    ).join(Batch, Class.id == Batch.class_id)\
     .join(MentorAssignment, Batch.id == MentorAssignment.batch_id)\
     .filter(MentorAssignment.mentor_id == current_user.id, MentorAssignment.is_active == True)\
     .distinct().order_by(Class.name, Batch.name).all()

    unique_classes = sorted(list(set([row.class_name for row in filter_data_query])))
    unique_batches = sorted(list(set([row.batch_name for row in filter_data_query])))

    filter_data = { 'classes': unique_classes, 'batches': unique_batches }
    
    return render_template('sessions_dashboard.html', 
                           live_sessions=live_sessions, 
                           upcoming_sessions=upcoming_sessions,
                           filter_data=filter_data)

@mentor_bp.route('/session/<int:session_id>/live')
@login_required
@role_required('mentor')
def live_session(session_id):
    session = Session.query.get_or_404(session_id)
    
    if session.assignment.mentor_id != current_user.id:
        abort(403)
        
    now = datetime.now(timezone.utc)
    session_end_time = session.start_time + timedelta(hours=1)
    if not (session.status == "In Progress" or (session.start_time <= now < session_end_time and session.status == "Upcoming")):
        flash("This session is not currently live or has already been completed.", "warning")
        return redirect(url_for('mentor.sessions'))

    mentees_in_batch = session.assignment.batch.mentees.join(User).order_by(User.name).all()
    approved_leave_mentee_ids = {req.mentee_id for req in session.leave_requests if req.status == 'Approved'}
    
    mentees = []
    for mentee_profile in mentees_in_batch:
        mentees.append({
            'profile': mentee_profile,
            'has_approved_leave': mentee_profile.user_id in approved_leave_mentee_ids
        })

    return render_template('mentor/live_session.html', session=session, mentees=mentees)

@mentor_bp.route('/leave_requests')
@login_required
@role_required('mentor')
def leave_requests():
    pending_requests = LeaveRequest.query\
        .join(Session).join(MentorAssignment)\
        .filter(MentorAssignment.mentor_id == current_user.id)\
        .filter(LeaveRequest.status == 'Pending')\
        .order_by(LeaveRequest.requested_at.asc()).all()
    
    return render_template('mentor/leave_requests.html', requests=pending_requests)

@mentor_bp.route('/completed_sessions')
@login_required
@role_required('mentor')
def completed_sessions():
    completed_and_missed_sessions = Session.query.join(MentorAssignment).filter(
        MentorAssignment.mentor_id == current_user.id,
        Session.status.in_(['Completed', 'Missed'])
    ).order_by(Session.start_time.desc()).all()
    
    return render_template('completed_sessions.html', sessions=completed_and_missed_sessions)

@mentor_bp.route('/session/<int:session_id>/details')
@login_required
@role_required('mentor')
def session_details(session_id):
    session = Session.query.get_or_404(session_id)
    if session.assignment.mentor_id != current_user.id:
        abort(403)

    models_to_check = {
        'Placement Information': PlacementInformation, 'Research Record': ResearchRecord, 
        'Academic Mark Details': AcademicSemesterMarkDetails, 'Awards and Achievements': AwardsAndAchievements, 
        'Co-Curricular Activity': CocurricularActivityRecord, 'Extra-Curricular Activity': ExtracurricularActivityRecord,
        'Internship Information': InternshipInformation, 'Mentor Meeting Details': MentorMeetingDetails,
        'Honors Or Minors Marks': HonorsMinorMarksDetails
    }
    
    mentees_in_batch = session.assignment.batch.mentees.join(User).order_by(User.name).all()
    all_data = {}

    for mentee_profile in mentees_in_batch:
        mentee_user = mentee_profile.user
        mentee_records = {}
        for name, model in models_to_check.items():
            records = model.query.filter_by(session_id=session.id, mentee_id=mentee_user.id).all()
            if records: mentee_records[name] = [model_to_dict(r) for r in records]
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

@mentor_bp.route('/my_batches')
@login_required
@role_required('mentor')
def my_batches():
    assignments = MentorAssignment.query.filter_by(mentor_id=current_user.id, is_active=True).join(Batch).order_by(Batch.name).all()
    return render_template('mentor/my_batches.html', assignments=assignments)

@mentor_bp.route('/batch/<int:batch_id>')
@login_required
@role_required('mentor')
def view_batch(batch_id):
    assignment = MentorAssignment.query.filter_by(mentor_id=current_user.id, batch_id=batch_id, is_active=True).first_or_404()
    batch = Batch.query.get_or_404(batch_id)
    mentees = MenteeProfile.query.filter_by(batch_id=batch_id).join(User).order_by(User.name).all()
    return render_template('mentor/view_batch.html', batch=batch, mentees=mentees)

@mentor_bp.route('/mentee/<int:user_id>')
@login_required
@role_required('mentor')
def view_mentee(user_id):
    mentee_user = User.query.filter_by(id=user_id, role='mentee').first_or_404()
    mentee_profile = mentee_user.mentee_profile
    if not mentee_profile: abort(404)
    is_assigned = MentorAssignment.query.filter_by(mentor_id=current_user.id, batch_id=mentee_profile.batch_id, is_active=True).first()
    if not is_assigned: abort(403)
    latest_academic_record = AcademicSemesterMarkDetails.query.filter_by(mentee_id=user_id).order_by(AcademicSemesterMarkDetails.id.desc()).first()
    display_profile = {
        'semester': latest_academic_record.semester if latest_academic_record else (mentee_profile.semester if mentee_profile.semester else 'N/A'),
        'gpa': latest_academic_record.gpa if latest_academic_record else (mentee_profile.gpa if mentee_profile.gpa is not None else 'N/A')
    }
    return render_template('mentor/view_mentee.html', mentee_user=mentee_user, mentee_profile=mentee_profile, display_profile=display_profile)

@mentor_bp.route('/mentee/<int:user_id>/download_report')
@login_required
@role_required('mentor')
def download_report(user_id):
    mentee_user = User.query.filter_by(id=user_id, role='mentee').first_or_404()
    mentee_profile = mentee_user.mentee_profile

    if not mentee_profile:
        abort(404)

    is_assigned = MentorAssignment.query.filter_by(mentor_id=current_user.id, batch_id=mentee_profile.batch_id, is_active=True).first()
    if not is_assigned:
        abort(403)

    pdf_bytes, filename = generate_mentee_full_report(user_id)

    if pdf_bytes is None:
        flash("Could not generate report.", "danger")
        return redirect(url_for('mentor.view_mentee', user_id=user_id))

    response = Response(
        pdf_bytes,
        mimetype='application/pdf'
    )
    response.headers['Content-Disposition'] = f'attachment;filename={filename}'
    return response