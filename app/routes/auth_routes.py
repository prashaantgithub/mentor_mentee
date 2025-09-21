from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, current_user, login_required
from ..models import User, MenteeProfile
from .. import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        role = request.form.get('role')
        remember = True if request.form.get('remember') else False

        user = None
        if role == 'mentee':
            mentee_profile = MenteeProfile.query.filter_by(reg_num=identifier).first()
            if mentee_profile:
                user = mentee_profile.user
        else: # For admin and mentor
            user = User.query.filter_by(email=identifier).first()
        
        # Now check if user exists, password is correct, AND role matches
        if user and user.role == role and user.check_password(password):
            login_user(user, remember=remember)
            
            if user.role == 'mentee' and not user.mentee_profile.profile_complete:
                return redirect(url_for('mentee.dashboard'))

            if user.must_change_password:
                flash('Welcome! For security, you must change your password before proceeding.', 'info')
                return redirect(url_for('main.profile'))
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard_redirect'))
        else:
            flash('Login Unsuccessful. Please check your credentials and role.', 'danger')
            # On failed login, re-render the page with the role they attempted to use
            return render_template('auth/login.html', selected_role=role)

    # For GET requests
    role_from_url = request.args.get('role', 'mentee')
    return render_template('auth/login.html', selected_role=role_from_url)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))