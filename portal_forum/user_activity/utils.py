from flask import url_for, redirect, flash, request

from portal_forum import db
from functools import wraps
from flask_login import current_user

from portal_forum.models import To_Delete
from portal_forum.models import TrackAlbums

def login_my_required(f):
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

def clear_target(target):
    for rate in target.rates:
        db.session.delete(rate)
    for opinion in target.opinions:
        db.session.delete(opinion)
    db.session.commit()

def clear_track(track):
    for scrap in track.scraps:
        clear_target(scrap)
        db.session.delete(scrap)
    for interpretation in track.interpretations:
        clear_target(interpretation)
        db.session.delete(interpretation)
    for translation in track.translations:
        clear_target(translation)
        db.session.delete(translation)
    for comment in track.comments:
        db.session.delete(comment)
    track_albums = TrackAlbums.query.filter_by(track_id=track.id).all()
    for track_album in track_albums:
        db.session.delete(track_album)
    db.session.commit()

def to_admin_delete(target_type, target_id):
    if not To_Delete.query.filter_by(type=target_type, target_id=target_id).first():
        to_delete = To_Delete(type=target_type, target_id=target_id)
        db.session.add(to_delete)
        db.session.commit()
        flash("Prośba o usunięcie została przesłana", "warning")
    else:
        flash("Prośba już wysłana", "warning")
