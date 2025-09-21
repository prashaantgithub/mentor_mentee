import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create the Flask app
app = create_app()

# Initialize extensions
migrate = Migrate(app, db)
manager = Manager(app)

# Add the 'db' command to our manager
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()