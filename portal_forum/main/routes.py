import os
import secrets
import sys
from datetime import datetime

from flask import Blueprint, flash, redirect, abort, request, json
from flask import render_template, url_for, current_app
from markupsafe import Markup
from sqlalchemy import desc, asc

from portal_forum import db
from portal_forum.models import Thread, Album, Track, To_Delete, Interpretation, Translation, Scrap
from flask_login import current_user, login_required

from portal_forum.user_activity.utils import clear_track, clear_target
from portal_forum.users.utils import check_image, save_image
from portal_forum.main.forms import AlbumForm

main = Blueprint('main', __name__)


def check_image():
    if current_user.is_authenticated:
        return url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        return "none"



@main.route('/')
@main.route('/home')
def home():
    return render_template('portal-home.html')

@main.route('/terms')
def terms():
    return render_template('terms.html', image_file=check_image())
@main.route('/movies')
def movies():
    return render_template('movies.html')

@main.route('/books')
def books():
    return render_template('books.html')

@main.route('/live')
def live():
    return render_template('live.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/forum')
def forum():
    threads = Thread.query.order_by(desc(Thread.date_last_update)).limit(5).all()
    tracks = Track.query.order_by(desc(Track.date_last_update)).limit(5).all()
    return render_template('forum-home.html', image_file=check_image(), threads=threads, tracks=tracks)



@main.route('/admin_panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    albums = Album.query.all()
    to_delete_requests = To_Delete.query.all()
    to_deletes = []
    for source in to_delete_requests:
        element = {}
        if source.type == "thread":
            thread = Thread.query.get_or_404(source.target_id)
            element["id"] = thread.id
            element["label"] = 'wątek'
            element["type"] = 'thread'
            element["name"] = thread.topic
            element["author"] = thread.author.username
        elif source.type == "track":
            '''print("_____________________________________________________-", file=sys.stderr)
            print(source.target_id, file=sys.stderr)
            print(Track.query.all(), file=sys.stderr)
            print(Track.query.filter_by(id=source.target_id).first(), file=sys.stderr)
            print("_____________________________________________________", file=sys.stderr)'''
            track = Track.query.get_or_404(source.target_id)
            element["id"] = track.id
            element["label"] = 'utwór'
            element["type"] = 'track'
            element["name"] = track.title
            element["author"] = track.author.username
        elif source.type == "interpretation":
            interpretation = Interpretation.query.get_or_404(source.target_id)
            element["id"] = interpretation.id
            element["label"] = 'interpretacja'
            element["type"] = 'interpretation'
            element["name"] = interpretation.title
            element["track_id"] = interpretation.track_id
            element["author"] = interpretation.author.username
        elif source.type == "translation":
            translation = Translation.query.get_or_404(source.target_id)
            element["id"] = translation.id
            element["label"] = 'tłumaczenie'
            element["type"] = 'translation'
            element["name"] = translation.title
            element["track_id"] = translation.track_id
            element["author"] = translation.author.username
        to_deletes.append(element)

    return render_template('admin_panel.html', image_file=check_image(), title="Panel administracyjny",
                           albums=albums, to_deletes=to_deletes)

def save_image(image):
    rnd_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    image_name = rnd_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static/album_covers', image_name)
    image.save(image_path)
    return image_name

@main.route('/album//create', methods=['GET', 'POST'])
@login_required
def create_album():
    image_file = "album_covers/default.jpg"
    if not current_user.is_admin:
        abort(403)
    form = AlbumForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_image(form.picture.data)
            album = Album(title=form.title.data, date_release=form.date_release.data, description=form.description.data, image_file=image_file)
        else:
            album = Album(title=form.title.data, date_release=form.date_release.data, description=form.description.data)


        db.session.add(album)
        db.session.commit()
        flash('Album dodano pomyślnie!', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('create_album.html', title="Dodaj album",
                           form=form, image_file=check_image(), image_album=image_file)


@main.route('/album/<int:album_id>/update', methods=['GET', 'POST'])
@login_required
def update_album(album_id):

    if not current_user.is_admin:
        abort(403)
    album = Album.query.get_or_404(album_id)
    form = AlbumForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_image(form.picture.data)
            album.image_file = image_file
        album.title = form.title.data
        album.date_release = form.date_release.data
        album.description = form.description.data
        db.session.commit()
        flash("Album został zaktualizowany!", 'success')
        return redirect(url_for('main.admin_panel'))
    elif request.method == "GET":
        form.title.data = album.title
        form.description.data = album.description
        form.date_release.data = album.date_release
        image_file = album.image_file
    return render_template('create_album.html', title="Edytuj album",
                           form=form, image_file=check_image(), image_album=image_file)


@main.route('/request_discard/type/<string:target_type>/<int:target_id>/delete', methods=['POST', 'GET'])
@login_required
def discard_request(target_id, target_type):
    if not current_user.is_admin:
        abort(403)
    target = To_Delete.query.filter_by(target_id=target_id, type=target_type).first()
    if target:
        db.session.delete(target)
        db.session.commit()

        flash("Prośba usunięta", 'success')
    return redirect(url_for('main.admin_panel'))


def delete_thread(thread):
    for post in thread.threads:
        db.session.delete(post)
    db.session.delete(thread)
    db.session.commit()


def delete_track(track):
    clear_track(track)
    db.session.delete(track)
    db.session.commit()


def delete_interpretation(interpretation):
    clear_target(interpretation)
    db.session.delete(interpretation)
    db.session.commit()


def delete_translation(translation):
    clear_target(translation)
    db.session.delete(translation)
    db.session.commit()


@main.route('/target/<string:target_type>/<int:target_id>/delete', methods=['POST', 'GET'])
@login_required
def delete_source(target_id, target_type):
    if not current_user.is_admin:
        abort(403)
    if target_type == "thread":
        target = Thread.query.get_or_404(target_id)
        delete_thread(target)
    elif target_type == "track":
        target = Track.query.get_or_404(target_id)
        delete_track(target)
    elif target_type == "interpretation":
        target = Interpretation.query.get_or_404(target_id)
        delete_interpretation(target)
    elif target_type == "translation":
        target = Translation.query.get_or_404(target_id)
        delete_translation(target)

    flash("Post usunięty", 'success')
    return redirect(url_for('main.discard_request', target_id=target_id, target_type=target_type))


@main.route('/album/<int:album_id>/delete', methods=['POST'])
@login_required
def delete_album(album_id):
    if not current_user.is_admin:
        abort(403)
    album = Album.query.get_or_404(album_id)
    db.session.delete(album)
    db.session.commit()
    flash("Album usunięty", 'success')
    return redirect(url_for('main.admin_panel'))


def publish_target(target, action):
    if action == "publish":
        target.published = 1;
    elif action == "unpublish":
        target.published = 0;


def is_published(track):
    if track.published == 1:
        return True
    else:
        return False


@main.route('/publish/<string:target_type>/<int:target_id>/<string:action_type>', methods=['POST', 'GET'])
@login_required
def publish(target_id, target_type, action_type):
    if not current_user.is_admin:
        abort(403)
    if target_type == "track":
        target = Track.query.get_or_404(target_id)
        publish_target(target, action_type)
        db.session.commit()
        return redirect(url_for('user_activity.track', track_id=target.id))
    elif target_type == "interpretation":
        target = Interpretation.query.get_or_404(target_id)
        action_type = action_type
        publish_target(target, action_type)
        db.session.commit()
        return redirect(url_for('user_activity.interpretation', interpretation_id=target_id, track_id=target.track_id))
    elif target_type == "translation":
        target = Translation.query.get_or_404(target_id)
        publish_target(target, action_type)
        db.session.commit()
        return redirect(url_for('user_activity.translation', translation_id=target_id, track_id=target.track_id))
    elif target_type == "scrap":
        target = Scrap.query.get_or_404(target_id)
        publish_target(target, action_type)
        db.session.commit()
        return redirect(url_for('user_activity.scraps', track_id=target.track_id))

@main.route('/portal/albums', methods=['GET', 'POST'])
def albums():
    albums = set()
    tracks_published = Track.query.filter_by(published=1).all()
    for track in tracks_published:
        for album in track.albums:
            albums.add(album)

    albums = list(albums)

    #albums = Album.query.filter_by().paginate(page=strona, per_page=5)
    return render_template('portal-albums.html', title="Albumy", albums=albums)

@main.route('/portal/album/<int:album_id>', methods=['GET', 'POST'])
def album(album_id):
    this_album = Album.query.get_or_404(album_id)
    tracks_all = Track.query.filter_by(published=1)
    tracks = list()
    for track in tracks_all:
        print("_____________________________________________________-", file=sys.stderr)
        print(track,track.published, file=sys.stderr)
        for album in track.albums:
            if album == this_album:
                tracks.append(track)
                continue

    description = Markup(this_album.description)

    return render_template('portal-album.html', title=album.title, description=description, tracks=tracks, album=this_album)

@main.route('/portal/tracks', methods=['GET', 'POST'])
def tracks():
    strona = request.args.get('strona', 1, type=int)
    tracks = Track.query.filter_by(published=1).order_by(desc(Track.date_last_update)).paginate(page=strona, per_page=5)
    return render_template('portal-tracks.html', title="Utwory", tracks=tracks)


@main.route('/portal/track/<int:track_id>', methods=['GET', 'POST'])
def track(track_id):
    track = Track.query.get_or_404(track_id)
    this_image_file = track.albums[0].image_file
    if is_published(track):
        tags = Markup(track.lyrics)
        return render_template('portal-track.html', title=track.title, track=track, tags=tags, this_image_file=this_image_file)
    else:
        return redirect(url_for("main.home"))


@main.route('/portal/track/<int:track_id>/scraps', methods=['GET', 'POST'])
def scraps(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics_with_scraps)
    scrap_descriptions = []
    scraps_published = []
    scraps = track.scraps
    for scrap in scraps:
        id = scrap.id
        scrap_descriptions.append({'id': id, 'description': scrap.description})
        scraps_published.append({'id': id, 'is_published': scrap.published})
    scrap_descriptions = json.dumps(scrap_descriptions)
    scraps_published = json.dumps(scraps_published)
    return render_template('portal-scraps.html', title=track.title, image_file=check_image(),
                           scraps_published=scraps_published, track=track, tags=tags,
                           scrap_descriptions=scrap_descriptions)


@main.route('/portal/track/<int:track_id>/interpretations', methods=['GET', 'POST'])
def interpretations(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    interpretations = Interpretation.query. \
        filter_by(track_id=track.id, published=1). \
        order_by(asc(Interpretation.date_posted))

    return render_template('portal-interpretations.html', title=track.title, image_file=check_image(),
                           track=track, tags=tags, interpretations=interpretations)


@main.route('/portal/track/<int:track_id>/interpretation/<int:interpretation_id>', methods=['GET', 'POST'])
def interpretation(track_id, interpretation_id):
    track = Track.query.get_or_404(track_id)
    interpretation = Interpretation.query.get_or_404(interpretation_id)
    if is_published(interpretation):
        tags = Markup(track.lyrics)
        interpretation_text = Markup(interpretation.text)
        return render_template('portal-interpretation.html', title=track.title,
                               track=track, tags=tags, interpretation=interpretation,
                               interpretation_text=interpretation_text)
    else:
        return redirect(url_for("main.home"))


@main.route('/portal/track/<int:track_id>/translations', methods=['GET', 'POST'])
def translations(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    translations = Translation.query. \
        filter_by(track_id=track.id, published=1). \
        order_by(asc(Translation.date_posted))

    return render_template('portal-translations.html', title=track.title, image_file=check_image(),
                           track=track, tags=tags, translations=translations)


@main.route('/portal/track/<int:track_id>/translation/<int:translation_id>', methods=['GET', 'POST'])
def translation(track_id, translation_id):
    track = Track.query.get_or_404(track_id)
    translation = Translation.query.get_or_404(translation_id)
    if is_published(translation):
        tags = Markup(track.lyrics)
        translation_text = Markup(translation.lyrics_trans)
        return render_template('portal-translation.html', title=track.title,
                               track=track, tags=tags, translation=translation,
                               translation_text=translation_text)
    else:
        return redirect(url_for("main.home"))
