from flask import Blueprint, render_template, redirect, url_for, abort, request, flash, current_app
from flask_login import current_user, login_required
from ..models import User
from .. import db
import os
from werkzeug.utils import secure_filename
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'mentor':
        return redirect(url_for('mentor.dashboard'))
    elif current_user.role == 'mentee':
        return redirect(url_for('mentee.dashboard'))
    else:
        abort(403)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload_picture':
            if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                profile_pic = request.files['profile_pic']
                try:
                    filename = secure_filename(profile_pic.filename)
                    unique_filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{os.path.splitext(filename)[1]}"
                    upload_path = os.path.join(current_app.root_path, 'static/img/profiles')
                    os.makedirs(upload_path, exist_ok=True)
                    file_path = os.path.join(upload_path, unique_filename)
                    profile_pic.save(file_path)
                    current_user.profile_picture = f'/static/img/profiles/{unique_filename}'
                    db.session.commit()
                    flash('Profile picture updated successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'An error occurred while uploading the picture: {e}', 'danger')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            else:
                try:
                    current_user.set_password(new_password)
                    current_user.must_change_password = False
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('main.dashboard_redirect'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'An error occurred: {e}', 'danger')

        elif action == 'update_mentor_profile' and current_user.role == 'mentor':
            try:
                mentor_profile = current_user.mentor_profile
                email = request.form.get('email', '').strip().lower()

                if not email.endswith('@christuniversity.in'):
                    flash('Invalid email domain. Please use your official ...@christuniversity.in email.', 'danger')
                    return redirect(url_for('main.profile'))
                
                existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
                if existing_user:
                    flash('This email address is already in use.', 'danger')
                    return redirect(url_for('main.profile'))

                current_user.email = email
                mentor_profile.department = request.form.get('department')
                mentor_profile.cabin_block = request.form.get('cabin_block')
                mentor_profile.cabin_floor = request.form.get('cabin_floor')
                mentor_profile.cabin_number = request.form.get('cabin_number')
                mentor_profile.profile_complete = True

                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while updating profile: {e}', 'danger')
        
        elif action == 'update_mentee_profile' and current_user.role == 'mentee':
            try:
                # This logic is now handled in mentee_routes.py, but keeping it here for the profile page edit modal
                mentee_profile = current_user.mentee_profile
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
                mentee_profile.hostel_name = request.form.get('hostel_name')
                mentee_profile.pg_owner_name = request.form.get('pg_owner_name')
                mentee_profile.pg_owner_mobile = request.form.get('pg_owner_mobile')
                mentee_profile.residence_address = request.form.get('residence_address')

                db.session.commit()
                flash('Your profile has been updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while updating your profile: {e}', 'danger')
                
        return redirect(url_for('main.profile'))
            
    return render_template('profile.html')