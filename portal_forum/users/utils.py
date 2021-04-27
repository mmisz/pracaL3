from flask import url_for, redirect, request, current_app
from flask_login import current_user
import secrets
import os
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('users.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function

def check_image():
    if current_user.is_authenticated:
        return url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        return "none"

def save_image(image):
    rnd_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    image_name = rnd_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static/profile_pics', image_name)
    image.save(image_path)
    return image_name