from functools import wraps
from flask import abort, current_app, Blueprint
from flask_login import current_user, login_required
from datetime import datetime, date
import pytz

utils_bp = Blueprint('utils', __name__)

LOCAL_TIMEZONE_NAME = 'Asia/Kolkata'

def get_local_timezone():
    return pytz.timezone(current_app.config.get('LOCAL_TIMEZONE', LOCAL_TIMEZONE_NAME))

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role_name:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def timestamp_to_local(dt, format_type='default'):
    if dt is None:
        return ""
    
    local_timezone = get_local_timezone()
    
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt_obj = datetime.fromisoformat(dt)
            else:
                dt_obj = date.fromisoformat(dt)
        except ValueError:
            return str(dt)
    elif isinstance(dt, (datetime, date)):
        dt_obj = dt
    else:
        return str(dt)

    if isinstance(dt_obj, date) and not isinstance(dt_obj, datetime):
        dt_obj = datetime.combine(dt_obj, datetime.min.time())

    if dt_obj.tzinfo is None:
        utc_dt = dt_obj.replace(tzinfo=pytz.utc)
    else:
        utc_dt = dt_obj.astimezone(pytz.utc)

    local_dt = utc_dt.astimezone(local_timezone)

    if format_type == 'full':
        return local_dt.strftime('%d %b %Y, %I:%M %p')
    elif format_type == 'date_only':
        return local_dt.strftime('%d/%m/%Y')
    elif format_type == 'time_only':
        return local_dt.strftime('%I:%M %p')
    return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')

def init_app_utils(app):
    app.jinja_env.filters['timestamp_to_local'] = timestamp_to_local