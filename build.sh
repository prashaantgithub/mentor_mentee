#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Explicitly set FLASK_APP for the following commands
export FLASK_APP=run:app

# Run database migrations
echo "--- Running Database Migrations ---"
flask db upgrade

# Create the admin user
echo "--- Seeding Admin User ---"
flask create-admin

echo "--- Build Complete ---"