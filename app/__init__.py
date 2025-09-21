from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import timedelta
from markupsafe import Markup, escape

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def nl2br(value):
    if value is None:
        return ""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') for p in escape(value).split('\n\n'))
    return Markup(result)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    from . import models
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.mentor_routes import mentor_bp
    from .routes.mentee_routes import mentee_bp
    from .routes.api_routes import api_bp
    from .utils.__init__ import init_app_utils

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp) # FIX: Removed url_prefix='/auth'
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(mentor_bp, url_prefix='/mentor')
    app.register_blueprint(mentee_bp, url_prefix='/mentee')
    app.register_blueprint(api_bp, url_prefix='/api')

    init_app_utils(app) 
    app.jinja_env.globals['timedelta'] = timedelta
    app.jinja_env.filters['nl2br'] = nl2br
    
    return app