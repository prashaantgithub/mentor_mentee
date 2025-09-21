# app/commands.py

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from .models import User
from . import db

@click.command(name='create-admin')
@with_appcontext
def create_admin_command():
    """Creates the admin user if it doesn't exist."""
    
    # Check if admin user already exists
    if User.query.filter_by(email='admin@christ.in').first():
        print('Admin user already exists.')
        return

    # Create the new admin user
    admin_user = User(
        email='admin@christ.in',
        password_hash=generate_password_hash('admin', method='pbkdf2:sha256'),
        name='Admin',
        role='admin'
    )
    db.session.add(admin_user)
    db.session.commit()
    print('Admin user created successfully.')