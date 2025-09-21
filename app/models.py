from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from sqlalchemy.orm import foreign

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=False, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(200), default='/static/img/default_profile.png')
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    must_change_password = db.Column(db.Boolean, default=False)
    admin_profile = db.relationship('AdminProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    mentor_profile = db.relationship('MentorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    mentee_profile = db.relationship('MenteeProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

class MentorProfile(db.Model):
    __tablename__ = 'mentor_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    department = db.Column(db.String(100))
    level = db.Column(db.String(50))
    cabin_block = db.Column(db.String(50))
    cabin_floor = db.Column(db.String(50))
    cabin_number = db.Column(db.String(50))
    profile_complete = db.Column(db.Boolean, default=False, nullable=False, server_default='false')

class MenteeProfile(db.Model):
    __tablename__ = 'mentee_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    reg_num = db.Column(db.String(50), unique=True, nullable=False, index=True)
    admission_number = db.Column(db.String(50))
    year_of_joining = db.Column(db.Integer)
    programme = db.Column(db.String(100))
    department = db.Column(db.String(100))
    residential_phone = db.Column(db.String(20))
    personal_cell = db.Column(db.String(20))
    dob = db.Column(db.Date)
    age = db.Column(db.Integer)
    blood_group = db.Column(db.String(10))
    father_name = db.Column(db.String(100))
    father_education = db.Column(db.String(100))
    father_occupation = db.Column(db.String(100))
    father_phone = db.Column(db.String(20))
    father_email = db.Column(db.String(120))
    mother_name = db.Column(db.String(100))
    mother_education = db.Column(db.String(100))
    mother_occupation = db.Column(db.String(100))
    mother_phone = db.Column(db.String(20))
    mother_email = db.Column(db.String(120))
    family_income = db.Column(db.String(50))
    siblings = db.Column(db.Integer)
    local_residence_type = db.Column(db.String(50))
    guardian_name = db.Column(db.String(100))
    guardian_relationship = db.Column(db.String(100))
    hostel_location = db.Column(db.String(50))
    hostel_name = db.Column(db.String(100))
    pg_owner_name = db.Column(db.String(100))
    pg_owner_mobile = db.Column(db.String(20))
    residence_address = db.Column(db.Text)
    semester = db.Column(db.String(50))
    gpa = db.Column(db.Float)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    archive_label = db.Column(db.String(100), nullable=True, index=True)
    profile_complete = db.Column(db.Boolean, default=False, nullable=False, server_default='false')

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    batches = db.relationship('Batch', backref='class_model', lazy='dynamic', cascade='all, delete-orphan')
    mentees = db.relationship('MenteeProfile', backref='assigned_class', lazy='dynamic', cascade='all, delete-orphan')

class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    mentees = db.relationship('MenteeProfile', backref='batch', lazy='dynamic')
    assignments = db.relationship('MentorAssignment', backref='batch', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def mentor_assignment(self):
        return self.assignments.filter_by(is_active=True).first()

class MentorAssignment(db.Model):
    __tablename__ = 'mentor_assignments'
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    is_temporary = db.Column(db.Boolean, default=False)
    temp_start_date = db.Column(db.Date, nullable=True)
    temp_end_date = db.Column(db.Date, nullable=True)
    original_mentor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    sessions = db.relationship('Session', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref=db.backref('assignments', lazy='dynamic'))
    original_mentor = db.relationship('User', foreign_keys=[original_mentor_id], backref=db.backref('original_assignments', lazy='dynamic'))
    __table_args__ = (db.UniqueConstraint('mentor_id', 'batch_id', 'is_active', name='_mentor_batch_active_uc'),)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    mentor_assignment_id = db.Column(db.Integer, db.ForeignKey('mentor_assignments.id', ondelete='CASCADE'), nullable=False)
    session_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    status = db.Column(db.String(50), default='Upcoming')
    actual_start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    actual_end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    leave_requests = db.relationship('LeaveRequest', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    meeting_details = db.relationship('MentorMeetingDetails', backref='session', lazy='dynamic', cascade='all, delete-orphan')

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending', index=True)
    requested_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    actioned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    mentee = db.relationship('User', backref='leave_requests')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    mentee = db.relationship('User', backref='attendance')

class PlacementInformation(db.Model):
    __tablename__ = 'placement_information'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    company_name = db.Column(db.String(255))
    company_location = db.Column(db.String(255))
    interview_date = db.Column(db.Date)
    rounds_attended = db.Column(db.Integer)
    internship_provided = db.Column(db.Boolean)
    annual_ctc = db.Column(db.Float)
    stipend_amount = db.Column(db.Float)
    interview_status = db.Column(db.String(100))

class ResearchRecord(db.Model):
    __tablename__ = 'research_records'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255))
    publication_name = db.Column(db.String(255))
    identifier_number = db.Column(db.String(100))
    publication_date = db.Column(db.Date)
    publication_type = db.Column(db.String(100))
    publication_status = db.Column(db.String(100))

class AcademicSemesterMarkDetails(db.Model):
    __tablename__ = 'academic_semester_mark_details'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    semester = db.Column(db.String(50))
    subject_code_name = db.Column(db.String(255))
    cia_1 = db.Column(db.Float)
    cia_2 = db.Column(db.Float)
    cia_3 = db.Column(db.Float)
    overall_cia = db.Column(db.Float)
    ese_attempt_1 = db.Column(db.Float)
    ese_attempt_2 = db.Column(db.Float)
    ese_attempt_3 = db.Column(db.Float)
    ese_attempt_4 = db.Column(db.Float)
    grade = db.Column(db.String(10))
    attendance_percentage = db.Column(db.Float)
    course_acceleration_deceleration = db.Column(db.String(50))
    gpa = db.Column(db.Float)
    cgpa = db.Column(db.Float)
    suggestions_by_mentor = db.Column(db.Text)

class HonorsMinorMarksDetails(db.Model):
    __tablename__ = 'honors_minor_marks_details'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    semester = db.Column(db.String(50))
    subject_code_name = db.Column(db.String(255))
    cia_1 = db.Column(db.Float)
    cia_2 = db.Column(db.Float)
    cia_3 = db.Column(db.Float)
    overall_cia = db.Column(db.Float)
    ese_attempt_1 = db.Column(db.Float)
    ese_attempt_2 = db.Column(db.Float)
    ese_attempt_3 = db.Column(db.Float)
    ese_attempt_4 = db.Column(db.Float)
    grade = db.Column(db.String(10))
    attendance_percentage = db.Column(db.Float)
    course_acceleration_deceleration = db.Column(db.String(50))
    gpa = db.Column(db.Float)
    cgpa = db.Column(db.Float)
    suggestions_by_mentor = db.Column(db.Text)

class MentorMeetingDetails(db.Model):
    __tablename__ = 'mentor_meeting_details'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    points_discussed = db.Column(db.Text)
    remarks_given = db.Column(db.Text)

class AwardsAndAchievements(db.Model):
    __tablename__ = 'awards_and_achievements'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    award_achievement_name = db.Column(db.String(255))
    award_achievement_type = db.Column(db.String(100))
    conducted_by = db.Column(db.String(255))
    date = db.Column(db.Date)

class CocurricularActivityRecord(db.Model):
    __tablename__ = 'cocurricular_activity_records'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    activity_name = db.Column(db.String(255))
    activity_type = db.Column(db.String(100))
    conducted_by = db.Column(db.String(255))
    date = db.Column(db.Date)

class ExtracurricularActivityRecord(db.Model):
    __tablename__ = 'extracurricular_activity_records'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    activity_name = db.Column(db.String(255))
    activity_type = db.Column(db.String(100))
    conducted_by = db.Column(db.String(255))
    date = db.Column(db.Date)

class InternshipInformation(db.Model):
    __tablename__ = 'internship_information'
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    company_name = db.Column(db.String(255))
    duration_from = db.Column(db.Date)
    duration_to = db.Column(db.Date)
    sem = db.Column(db.String(50))
    technology_domain = db.Column(db.String(255))
    internship_project_details = db.Column(db.Text)
    company_location = db.Column(db.String(255))
    internship_status = db.Column(db.String(100))