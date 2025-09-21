from fpdf import FPDF
from flask import current_app
import os
import io
from datetime import datetime, date
from .. import db
from ..models import (User, MenteeProfile, Session, MentorAssignment, PlacementInformation, ResearchRecord, 
                     AcademicSemesterMarkDetails, MentorMeetingDetails, AwardsAndAchievements, 
                     CocurricularActivityRecord, ExtracurricularActivityRecord, InternshipInformation,
                     HonorsMinorMarksDetails)
from .__init__ import timestamp_to_local

class ReportPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=False, margin=15)
        self.watermark_path = os.path.join(current_app.root_path, 'static', 'img', 'watermark.png')
        
        font_dir = os.path.join(current_app.root_path, 'static', 'fonts')
        
        try:
            self.add_font('Poppins', '', os.path.join(font_dir, 'Poppins-Regular.ttf'), uni=True)
            self.add_font('Poppins', 'B', os.path.join(font_dir, 'Poppins-Bold.ttf'), uni=True)
            self.add_font('Poppins', 'I', os.path.join(font_dir, 'Poppins-Italic.ttf'), uni=True)
            self.current_font_family = 'Poppins'
        except RuntimeError:
            self.set_font('Arial', '', 10)
            self.current_font_family = 'Arial'

    def add_watermark(self):
        if os.path.exists(self.watermark_path):
            page_w = self.w
            page_h = self.h
            img_w = 100
            img_h = 100
            x = (page_w - img_w) / 2
            y = (page_h - img_h) / 2
            self.image(self.watermark_path, x=x, y=y, w=img_w, h=img_h)
        
    def header(self):
        self.set_font(self.current_font_family, 'I', 9)
        self.cell(0, 10, 'Department of Computer Science and Engineering', 0, 0, 'L')
        self.set_font(self.current_font_family, 'B', 8)
        self.cell(0, 10, 'CHRIST', 0, 1, 'R')
        
    def footer(self):
        self.set_y(-15)
        self.set_font(self.current_font_family, 'I', 9)
        self.cell(0, 10, 'Mentoring Dairy', 0, 0, 'L')
        self.set_font(self.current_font_family, '', 9)
        self.cell(0, 10, str(self.page_no()), 0, 0, 'R')

    def chapter_title(self, title):
        self.ln(5)
        self.set_font(self.current_font_family, 'B', 12)
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(5)

    def academic_marks_header(self, col_widths):
        self.set_font(self.current_font_family, 'B', 7)
        self.set_fill_color(230,230,230)
        
        y1 = self.get_y()
        self.multi_cell(col_widths['s_no'], 14, 'S. No', 1, 'C', fill=True)
        x2 = self.get_x() + col_widths['s_no']
        self.set_xy(x2, y1)
        self.multi_cell(col_widths['subject'], 14, 'Subject Code / Name', 1, 'C', fill=True)
        x3 = x2 + col_widths['subject']
        self.set_xy(x3, y1)

        cia_width = col_widths['cia'] * 4
        self.multi_cell(cia_width, 7, 'CONTINUOUS INTERNAL ASSESSMENT (CIA)', 1, 'C', fill=True)
        x4 = x3 + cia_width
        self.set_xy(x4, y1)
        
        ese_width = col_widths['ese'] * 4
        self.multi_cell(ese_width, 7, 'END SEM EXAMINATION (ESE)', 1, 'C', fill=True)
        x5 = x4 + ese_width
        self.set_xy(x5, y1)
        
        self.multi_cell(col_widths['grade'], 14, 'GRADE', 1, 'C', fill=True)
        x6 = x5 + col_widths['grade']
        self.set_xy(x6, y1)

        self.multi_cell(col_widths['attendance'], 14, 'ATTENDANCE %', 1, 'C', fill=True)
        self.ln(0)

        self.set_xy(x3, y1 + 7)
        self.cell(col_widths['cia'], 7, 'CIA-1', 1, 0, 'C', fill=True)
        self.cell(col_widths['cia'], 7, 'CIA-2', 1, 0, 'C', fill=True)
        self.cell(col_widths['cia'], 7, 'CIA-3', 1, 0, 'C', fill=True)
        self.cell(col_widths['cia'], 7, 'Overall CIA', 1, 0, 'C', fill=True)
        
        self.set_xy(x4, y1 + 7)
        self.cell(col_widths['ese'], 7, 'ATTEMPT-1', 1, 0, 'C', fill=True)
        self.cell(col_widths['ese'], 7, 'ATTEMPT-2', 1, 0, 'C', fill=True)
        self.cell(col_widths['ese'], 7, 'ATTEMPT-3', 1, 0, 'C', fill=True)
        self.cell(col_widths['ese'], 7, 'ATTEMPT-4', 1, 0, 'C', fill=True)

        self.set_y(y1 + 14)

def generate_mentee_full_report(user_id):
    mentee_user = User.query.filter_by(id=user_id, role='mentee').first()
    if not mentee_user or not mentee_user.mentee_profile:
        return None, None
    mentee_profile = mentee_user.mentee_profile

    pdf = ReportPDF()
    current_font_family = pdf.current_font_family

    latest_academic_record = AcademicSemesterMarkDetails.query.filter_by(mentee_id=user_id).order_by(AcademicSemesterMarkDetails.id.desc()).first()
    semester_for_filename = latest_academic_record.semester if latest_academic_record and latest_academic_record.semester else "Full_Report"
    
    filename = f"{mentee_user.name.replace(' ', '_')}_{mentee_profile.reg_num}_{semester_for_filename}.pdf"

    pdf.add_page('P')
    pdf.add_watermark()
    pdf.ln(5)
    
    pdf.set_font(current_font_family, 'B', 12)
    pdf.cell(0, 10, 'MENTEE RECORD', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "Personal Profile", 'B', 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(current_font_family, '', 10)
    pdf.cell(40, 7, 'Name:')
    pdf.cell(0, 7, mentee_user.name if mentee_user.name else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'Admission Number:')
    pdf.cell(50, 7, mentee_profile.admission_number if mentee_profile.admission_number else 'N/A', 'B', 0)
    pdf.cell(40, 7, 'Register Number:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.reg_num if mentee_profile.reg_num else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'Year of Joining:')
    pdf.cell(50, 7, str(mentee_profile.year_of_joining) if mentee_profile.year_of_joining else 'N/A', 'B', 0)
    pdf.cell(40, 7, 'Programme:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.programme if mentee_profile.programme else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'Department:')
    pdf.cell(0, 7, mentee_profile.department if mentee_profile.department else 'N/A', 'B')
    pdf.ln(8)
    
    profile_pic_path = mentee_user.profile_picture[1:] if mentee_user.profile_picture.startswith('/') else mentee_user.profile_picture
    full_profile_pic_path = os.path.join(current_app.root_path, profile_pic_path)
    if os.path.exists(full_profile_pic_path):
        pdf.image(full_profile_pic_path, x=pdf.w - 40, y=30, w=30, h=40)
    
    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "Contact Details", 'B', 1, 'L')
    pdf.ln(2)

    pdf.set_font(current_font_family, '', 10)
    pdf.cell(40, 7, 'Address:')
    pdf.multi_cell(0, 7, mentee_profile.residence_address if mentee_profile.residence_address else 'N/A', 'B')
    pdf.ln(3)
    pdf.cell(40, 7, 'Residential Phone No:')
    pdf.cell(50, 7, mentee_profile.residential_phone if mentee_profile.residential_phone else 'N/A', 'B', 0)
    pdf.cell(40, 7, 'Personal Cell No:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.personal_cell if mentee_profile.personal_cell else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'E-mail:')
    pdf.cell(0, 7, mentee_user.email if mentee_user.email else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(15, 7, 'DOB:')
    pdf.cell(40, 7, timestamp_to_local(mentee_profile.dob, 'date_only') if mentee_profile.dob else 'N/A', 'B', 0)
    pdf.cell(15, 7, 'Age:', 0, 0, 'R')
    pdf.cell(20, 7, str(mentee_profile.age) if mentee_profile.age else 'N/A', 'B', 0)
    pdf.cell(30, 7, 'Blood Group:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.blood_group if mentee_profile.blood_group else 'N/A', 'B')
    pdf.ln(8)

    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "Family Details", 'B', 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(current_font_family, '', 10)
    pdf.cell(40, 7, "Father's Name:")
    pdf.cell(0, 7, mentee_profile.father_name if mentee_profile.father_name else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(25, 7, 'Education:')
    pdf.cell(40, 7, mentee_profile.father_education if mentee_profile.father_education else 'N/A', 'B', 0)
    pdf.cell(30, 7, 'Occupation:')
    pdf.cell(0, 7, mentee_profile.father_occupation if mentee_profile.father_occupation else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(25, 7, 'Phone No:')
    pdf.cell(40, 7, mentee_profile.father_phone if mentee_profile.father_phone else 'N/A', 'B', 0)
    pdf.cell(20, 7, 'Email:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.father_email if mentee_profile.father_email else 'N/A', 'B')
    pdf.ln(8)
    
    pdf.cell(40, 7, "Mother's Name:")
    pdf.cell(0, 7, mentee_profile.mother_name if mentee_profile.mother_name else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(25, 7, 'Education:')
    pdf.cell(40, 7, mentee_profile.mother_education if mentee_profile.mother_education else 'N/A', 'B', 0)
    pdf.cell(30, 7, 'Occupation:')
    pdf.cell(0, 7, mentee_profile.mother_occupation if mentee_profile.mother_occupation else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(25, 7, 'Phone No:')
    pdf.cell(40, 7, mentee_profile.mother_phone if mentee_profile.mother_phone else 'N/A', 'B', 0)
    pdf.cell(20, 7, 'Email:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.mother_email if mentee_profile.mother_email else 'N/A', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'Family Income:')
    pdf.cell(40, 7, mentee_profile.family_income if mentee_profile.family_income else 'N/A', 'B', 0)
    pdf.cell(40, 7, 'No. of Siblings:', 0, 0, 'R')
    pdf.cell(0, 7, str(mentee_profile.siblings) if mentee_profile.siblings is not None else 'N/A', 'B')
    pdf.ln(8)

    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "Local Residence: (Tick the relevant box)", 'B', 1, 'L')
    pdf.ln(2)

    pdf.set_font(current_font_family, '', 10)
    box_size = 4
    res_type = mentee_profile.local_residence_type.lower() if mentee_profile.local_residence_type else ''
    pdf.cell(20, 7, 'Parents')
    pdf.rect(pdf.get_x(), pdf.get_y() + (7-box_size)/2, box_size, box_size, 'D')
    if 'parents' in res_type: pdf.text(pdf.get_x() + 1, pdf.get_y() + 4.5, 'X')
    pdf.set_x(pdf.get_x() + box_size + 15)
    pdf.cell(20, 7, 'Hostel')
    pdf.rect(pdf.get_x(), pdf.get_y() + (7-box_size)/2, box_size, box_size, 'D')
    if 'hostel' in res_type: pdf.text(pdf.get_x() + 1, pdf.get_y() + 4.5, 'X')
    pdf.set_x(pdf.get_x() + box_size + 15)
    pdf.cell(25, 7, 'Relatives')
    pdf.rect(pdf.get_x(), pdf.get_y() + (7-box_size)/2, box_size, box_size, 'D')
    if 'relatives' in res_type: pdf.text(pdf.get_x() + 1, pdf.get_y() + 4.5, 'X')
    pdf.set_x(pdf.get_x() + box_size + 15)
    pdf.cell(55, 7, 'Private PG / Rented House')
    pdf.rect(pdf.get_x(), pdf.get_y() + (7-box_size)/2, box_size, box_size, 'D')
    if 'pg' in res_type or 'rented' in res_type: pdf.text(pdf.get_x() + 1, pdf.get_y() + 4.5, 'X')
    pdf.ln(10)
    
    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "For Hostelites:", 0, 1, 'L')
    pdf.set_font(current_font_family, '', 10)
    pdf.cell(40, 7, 'Local Guardian\'s Name (LG):')
    pdf.cell(50, 7, mentee_profile.guardian_name if mentee_profile.guardian_name else '', 'B', 0)
    pdf.cell(40, 7, 'Relationship:', 0, 0, 'R')
    pdf.cell(0, 7, mentee_profile.guardian_relationship if mentee_profile.guardian_relationship else '', 'B')
    pdf.ln(8)
    pdf.cell(40, 7, 'Address:')
    pdf.cell(0, 7, '', 'B')
    pdf.ln(15)

    pdf.set_font(current_font_family, 'B', 10)
    pdf.cell(0, 7, "Private PG / Rented House:", 0, 1, 'L')
    pdf.set_font(current_font_family, '', 10)
    pdf.cell(40, 7, 'Address:')
    pdf.cell(0, 7, '', 'B')
    pdf.ln()

    def create_dynamic_table(title, Model, headers, fields, widths):
        pdf.add_page('L')
        pdf.add_watermark()
        pdf.chapter_title(title)
        records = Model.query.filter_by(mentee_id=user_id).all()
        
        x_start = (pdf.w - sum(widths)) / 2
        pdf.set_x(x_start)
        
        pdf.set_font(current_font_family, 'B', 8)
        pdf.set_fill_color(230,230,230)
        
        y1 = pdf.get_y()
        line_h = 5
        header_heights = []
        for i, header in enumerate(headers):
            lines = pdf.multi_cell(widths[i], line_h, header, split_only=True)
            header_heights.append(len(lines) * line_h)
        max_h = max(header_heights)
        max_h = max(max_h, 10)

        for i, header in enumerate(headers):
            x = pdf.get_x()
            text_y_pos = y1 + (max_h - header_heights[i]) / 2
            
            pdf.rect(x, y1, widths[i], max_h, 'DF')
            pdf.set_xy(x, text_y_pos)
            pdf.multi_cell(widths[i], line_h, header, 0, 'C')
            
            pdf.set_xy(x + widths[i], y1)

        pdf.ln(max_h)

        pdf.set_font(current_font_family, '', 8)
        
        data = []
        if records:
            for i, r in enumerate(records):
                row_data = [i + 1]
                for field_name, formatter in fields.items():
                    value = getattr(r, field_name)
                    row_data.append(formatter(value) if formatter else value)
                data.append(row_data)

            for row in data:
                y_before = pdf.get_y()
                x_current = x_start
                max_height = 10 
                for i, item in enumerate(row):
                    if widths[i] > 0:
                        lines = pdf.multi_cell(widths[i], 5, str(item) if item is not None else '', split_only=True)
                        max_height = max(max_height, len(lines) * 5)
                
                max_height = max(10, max_height)
                
                pdf.set_y(y_before)
                pdf.set_x(x_start)
                for i, item in enumerate(row):
                    x = pdf.get_x()
                    pdf.multi_cell(widths[i], max_height / (len(pdf.multi_cell(widths[i], 5, str(item) if item is not None else '', split_only=True)) or 1), str(item) if item is not None else '', 1, 'C')
                    pdf.set_xy(x + widths[i], y_before)
                pdf.ln(max_height)

        remaining_rows = 8 - len(data)
        if remaining_rows > 0:
            for _ in range(remaining_rows):
                pdf.set_x(x_start)
                for i in range(len(headers)):
                    pdf.cell(widths[i], 10, '', 1)
                pdf.ln()
    
    create_dynamic_table('Placement Information', PlacementInformation,
                 ['S. No', 'Company Name', 'Location', 'Interview Date', 'Rounds Attended', 'Internship Provided', 'Annual CTC (Rs.)', 'Stipend (Rs.)', 'Status'],
                 {'company_name': None, 'company_location': None, 'interview_date': lambda d: timestamp_to_local(d, 'date_only') if d else '', 'rounds_attended': None, 'internship_provided': lambda b: 'Yes' if b else 'No', 'annual_ctc': None, 'stipend_amount': None, 'interview_status': None},
                 [10, 35, 30, 25, 20, 25, 30, 30, 45])

    create_dynamic_table('Research Record', ResearchRecord,
                 ['S. No', 'Title', 'Conference/Journal', 'ISSN/ISBN', 'Date', 'Type', 'Status'],
                 {'title': None, 'publication_name': None, 'identifier_number': None, 'publication_date': lambda d: timestamp_to_local(d, 'date_only') if d else '', 'publication_type': None, 'publication_status': None},
                 [10, 60, 60, 35, 20, 45, 30])

    create_dynamic_table('Internship Information', InternshipInformation,
                 ['S. No', 'Company Name', 'Duration From', 'Duration To', 'Sem', 'Domain', 'Project Details', 'Location', 'Status'],
                 {'company_name': None, 'duration_from': lambda d: timestamp_to_local(d, 'date_only') if d else '', 'duration_to': lambda d: timestamp_to_local(d, 'date_only') if d else '', 'sem': None, 'technology_domain': None, 'internship_project_details': None, 'company_location': None, 'internship_status': None},
                 [10, 30, 20, 20, 10, 40, 50, 30, 40])

    create_dynamic_table('Co-Curricular Activity Record', CocurricularActivityRecord,
                 ['S. No', 'Activity Name', 'Activity Type', 'Conducted By', 'Date'],
                 {'activity_name': None, 'activity_type': None, 'conducted_by': None, 'date': lambda d: timestamp_to_local(d, 'date_only') if d else ''},
                 [15, 80, 60, 80, 25])

    create_dynamic_table('Extra-Curricular Activity Record', ExtracurricularActivityRecord,
                 ['S. No', 'Activity Name', 'Activity Type', 'Conducted By', 'Date'],
                 {'activity_name': None, 'activity_type': None, 'conducted_by': None, 'date': lambda d: timestamp_to_local(d, 'date_only') if d else ''},
                 [15, 80, 60, 80, 25])

    create_dynamic_table('Awards and Achievements', AwardsAndAchievements,
                 ['S. No', 'Award/Achievement Name', 'Type', 'Conducted By', 'Date'],
                 {'award_achievement_name': None, 'award_achievement_type': None, 'conducted_by': None, 'date': lambda d: timestamp_to_local(d, 'date_only') if d else ''},
                 [15, 80, 60, 80, 25])
                 
    semesters = db.session.query(AcademicSemesterMarkDetails.semester).filter_by(mentee_id=user_id).distinct().order_by(AcademicSemesterMarkDetails.semester).all()
    for sem in semesters:
        semester_name = sem[0]
        if not semester_name: continue
        pdf.add_page('L')
        pdf.add_watermark()
        pdf.chapter_title(f'ACADEMIC SEMESTER MARK DETAILS - {semester_name.upper()}')
        
        col_widths = {'s_no': 10, 'subject': 70, 'cia': 15, 'ese': 15, 'grade': 15, 'attendance': 22}
        
        x_start = (pdf.w - sum(col_widths.values())) / 2
        pdf.set_x(x_start)
        
        pdf.academic_marks_header(col_widths)
        
        pdf.set_font(current_font_family, '', 7)
        records = AcademicSemesterMarkDetails.query.filter_by(mentee_id=user_id, semester=semester_name).all()
        for i, r in enumerate(records):
            pdf.set_x(x_start)
            pdf.cell(col_widths['s_no'], 6, str(i+1), 1, 0, 'C')
            pdf.cell(col_widths['subject'], 6, r.subject_code_name or '', 1)
            pdf.cell(col_widths['cia'], 6, str(r.cia_1) if r.cia_1 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['cia'], 6, str(r.cia_2) if r.cia_2 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['cia'], 6, str(r.cia_3) if r.cia_3 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['cia'], 6, str(r.overall_cia) if r.overall_cia is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['ese'], 6, str(r.ese_attempt_1) if r.ese_attempt_1 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['ese'], 6, str(r.ese_attempt_2) if r.ese_attempt_2 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['ese'], 6, str(r.ese_attempt_3) if r.ese_attempt_3 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['ese'], 6, str(r.ese_attempt_4) if r.ese_attempt_4 is not None else '', 1, 0, 'C')
            pdf.cell(col_widths['grade'], 6, r.grade or '', 1, 0, 'C')
            pdf.cell(col_widths['attendance'], 6, str(r.attendance_percentage) if r.attendance_percentage is not None else '', 1, 0, 'C')
            pdf.ln()
        
        if len(records) < 8:
            for _ in range(8 - len(records)):
                pdf.set_x(x_start)
                pdf.cell(col_widths['s_no'], 6, '', 1)
                pdf.cell(col_widths['subject'], 6, '', 1)
                for _ in range(8): pdf.cell(col_widths['cia'], 6, '', 1)
                pdf.cell(col_widths['grade'], 6, '', 1)
                pdf.cell(col_widths['attendance'], 6, '', 1)
                pdf.ln()

        pdf.ln(5)
        pdf.set_x(x_start)
        pdf.cell(130, 7, f"GPA : {records[0].gpa if records and records[0].gpa else 'N/A'}", 1)
        pdf.cell(sum(col_widths.values()) - 130, 7, f"CGPA : {records[0].cgpa if records and records[0].cgpa else 'N/A'}", 1, 1)
        pdf.set_x(x_start)
        pdf.cell(sum(col_widths.values()), 7, f"Suggestions by Mentor to Improve: {records[0].suggestions_by_mentor if records and records[0].suggestions_by_mentor else ''}", 1, 1)
        pdf.ln(20)
        pdf.set_x(x_start)
        pdf.cell(130, 7, "Student Signature", 0, 0, 'L')
        pdf.cell(0, 7, "Mentor Signature", 0, 1, 'R')

    pdf.add_page('L')
    pdf.add_watermark()
    pdf.chapter_title('Mentor Meeting Details')
    meeting_records = MentorMeetingDetails.query.filter_by(mentee_id=user_id).join(Session).order_by(Session.start_time).all()
    
    headers = ['S. No', 'Date of Meeting', 'Points Discussed', 'Remarks Given', 'Mentee Signature', 'Mentor Signature']
    widths = [10, 30, 80, 80, 30, 30]
    
    x_start = (pdf.w - sum(widths)) / 2
    pdf.set_x(x_start)
    
    pdf.set_font(current_font_family, 'B', 8)
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font(current_font_family, '', 8)
    meeting_data = []
    if meeting_records:
        for i, r in enumerate(meeting_records):
            meeting_data.append([
                i+1, 
                timestamp_to_local(r.session.start_time, 'date_only') if r.session else '',
                r.points_discussed or '',
                r.remarks_given or '',
                '', ''
            ])
        
        for row in meeting_data:
            y_before = pdf.get_y()
            x_current = x_start
            max_height = 10 
            pdf.set_x(x_start + widths[0] + widths[1])
            points_lines = pdf.multi_cell(widths[2], 5, str(row[2]), split_only=True)
            pdf.set_x(x_start + widths[0] + widths[1] + widths[2])
            remarks_lines = pdf.multi_cell(widths[3], 5, str(row[3]), split_only=True)
            pdf.set_y(y_before)

            row_height = max(len(points_lines), len(remarks_lines), 1) * 5
            row_height = max(10, row_height)

            pdf.set_x(x_start)
            pdf.cell(widths[0], row_height, str(row[0]), 1, 0, 'C')
            pdf.cell(widths[1], row_height, str(row[1]), 1, 0, 'C')
            x_pos = pdf.get_x()
            pdf.multi_cell(widths[2], 5, str(row[2]), 1, 'L')
            pdf.set_xy(x_pos + widths[2], y_before)
            x_pos += widths[2]
            pdf.multi_cell(widths[3], 5, str(row[3]), 1, 'L')
            pdf.set_xy(x_pos + widths[3], y_before)
            pdf.cell(widths[4], row_height, str(row[4]), 1, 0)
            pdf.cell(widths[5], row_height, str(row[5]), 1, 1)

    num_data_rows = len(meeting_data)
    if num_data_rows < 8:
        for _ in range(8 - num_data_rows):
            pdf.set_x(x_start)
            for i in range(len(headers)):
                pdf.cell(widths[i], 10, '', 1)
            pdf.ln()

    return_file = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    return return_file.getvalue(), filename