import sys
from functools import wraps

from flask import render_template, url_for, redirect, flash, request, abort, Blueprint, g, json
from markupsafe import Markup
from sqlalchemy import desc, asc
from portal_forum.user_activity.forms import ThreadForm, PostForm, TrackForm, ScrapForm, InterpretationForm, \
    OpinionForm, TranslationForm, CommentForm
from portal_forum import db
from portal_forum.models import Thread, User, Thread_Post, Track, Album, Scrap, Track_Post, Interpretation, \
    Interpretation_Opinion, Translation_Opinion, Translation, Scrap_Rating, Translation_Rating, Interpretation_Rating, \
    Scrap_Opinion, To_Delete
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from portal_forum.users.utils import check_image
from portal_forum.user_activity.utils import clear_track, clear_target, to_admin_delete, login_my_required
import re

user_activity = Blueprint('user_activity', __name__)


@user_activity.route('/threads', methods=['GET', 'POST'])
def threads():
    strona = request.args.get('strona', 1, type=int)
    threads = Thread.query.order_by(desc(Thread.date_last_update)).paginate(page=strona, per_page=5)
    return render_template('threads.html', title="Wątki", image_file=check_image(), threads=threads)


@user_activity.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    tags = Markup(thread.description)
    posts = Thread_Post.query. \
        filter_by(thread=thread). \
        order_by(asc(Thread_Post.date_posted))
    replies = []
    for post in posts:
        replies.append(Markup(post.reply))
    return render_template('thread.html', title=thread.topic, image_file=check_image(), thread=thread, tags=tags,
                           posts=posts, replies=replies)


@user_activity.route('/thread/new', methods=['GET', 'POST'])
@login_my_required
def new_thread():
    form = ThreadForm()
    if form.validate_on_submit():
        thread = Thread(topic=form.topic.data, description=form.description.data, author=current_user)
        db.session.add(thread)
        db.session.commit()
        flash("Wątek został dodany", "success")
        return redirect(url_for('main.forum'))
    return render_template('create_thread.html', title="Nowy wątek",
                           legend="Rozpocznij nowy wątek", form=form, image_file=check_image())


@user_activity.route('/thread/<int:thread_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.author != current_user:
        abort(403)
    form = ThreadForm()
    if form.validate_on_submit():
        thread.topic = form.topic.data
        thread.description = form.description.data
        thread.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Wątek zaktualizowany!", 'success')
        return redirect(url_for('user_activity.thread', thread_id=thread.id))
    elif request.method == "GET":
        form.topic.data = thread.topic
        form.description.data = thread.description
    return render_template('create_thread.html', title="Edytuj wątek",
                           legend="Edytuj wątek", form=form, image_file=check_image(), thread_id=thread_id)


@user_activity.route('/thread/<int:thread_id>/delete', methods=['POST'])
@login_my_required
def delete_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.author != current_user and not current_user.is_admin:
        abort(403)
    if not current_user.is_admin and len(thread.threads) > 0:
        to_admin_delete('thread', thread_id)
        return redirect(url_for('user_activity.thread', thread_id=thread.id))
    elif current_user.is_admin and len(thread.threads) > 0:
        for post in thread.threads:
            db.session.delete(post)
        db.session.delete(thread)
        db.session.commit()
    elif len(thread.threads) == 0:
        db.session.delete(thread)
        db.session.commit()
    flash("Wątek usunięty", 'success')
    return redirect(url_for('user_activity.threads'))


@user_activity.route('/thread/<int:thread_id>/reply', methods=['GET', 'POST'])
@login_my_required
def thread_reply(thread_id):
    form = PostForm()
    if form.validate_on_submit():
        post = Thread_Post(reply=form.reply.data, author=current_user, thread_id=thread_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.thread', thread_id=thread_id))
    return render_template('thread_reply.html', title="Rozwiń wątek",
                           legend="Odpowiedz", form=form, image_file=check_image(),
                           thread_id=thread_id, reply_id=None)


@user_activity.route('/thread/<int:thread_id>/reply_to/<int:post_id>', methods=['GET', 'POST'])
@login_my_required
def quote_thread_post(thread_id, post_id):
    post = Thread_Post.query.get_or_404(post_id)
    form = PostForm()
    date_posted = datetime.strptime(str(post.date_posted), "%Y-%m-%d %H:%M:%S.%f")
    date_posted = date_posted.strftime('%Y-%m-%d %H:%M')
    quote = "<div>" \
            "<div style='background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;'>" \
            "<b>" + post.author.username + "</b> powiedział " + date_posted + \
            "</div>" \
            "<blockquote class='cke_contents_ltr blockquote'>" + post.reply + "</blockquote>" \
                                                                              "<p></p></div>"
    if form.validate_on_submit():
        post = Thread_Post(reply=form.reply.data, author=current_user, thread_id=thread_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.thread', thread_id=thread_id))
    elif request.method == "GET":
        form.reply.data = Markup(quote)
    return render_template('thread_reply.html', title="Rozwiń wątek",
                           legend="Odpowiedz użytkownikowi " + post.author.username, form=form,
                           image_file=check_image(),
                           thread_id=thread_id, reply_id=None)


@user_activity.route('/thread/<int:thread_id>/reply/<int:post_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_thread_post(post_id, thread_id):
    post = Thread_Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.reply = form.reply.data
        post.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Odpowiedź została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.thread', thread_id=thread_id))
    elif request.method == "GET":
        form.reply.data = post.reply
    return render_template('thread_reply.html', title="Edytuj odpowiedź",
                           legend="Edytuj odpowiedź", form=form,
                           image_file=check_image(), thread_id=thread_id)


@user_activity.route('/thread/<int:thread_id>/reply/<int:post_id>/delete', methods=['POST'])
@login_my_required
def delete_thread_post(thread_id, post_id):
    post = Thread_Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Odpowiedź została usunięta", 'success')
    return redirect(url_for('user_activity.thread', thread_id=thread_id))


@login_my_required
@user_activity.route('/track/<int:track_id>', methods=['GET', 'POST'])
def track(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    comments = Track_Post.query. \
        filter_by(track=track). \
        order_by(asc(Track_Post.date_posted))
    tags_description = Markup(track.description)

    replies = []
    for comment in comments:
        replies.append(Markup(comment.reply))

    return render_template('track.html', title=track.title, image_file=check_image(), track=track, tags=tags,
                           tags_description=tags_description, comments=comments, replies=replies)


@user_activity.route('/tracks', methods=['GET', 'POST'])
@login_my_required
def tracks():
    strona = request.args.get('strona', 1, type=int)
    tracks = Track.query.order_by(desc(Track.date_last_update)).paginate(page=strona, per_page=5)
    return render_template('tracks.html', title="Utwory", image_file=check_image(), tracks=tracks)


@user_activity.route('/tracks/new', methods=['GET', 'POST'])
@login_my_required
def new_track():
    form = TrackForm()
    albums = Album.query.all()

    if form.validate_on_submit():
        albums_list = request.form.getlist("albums")
        tags = form.lyrics.data
        tags = tags.replace("<p>", '')
        tags = tags.replace("</p>", "<br/>")
        tags = tags.replace("&oacute;", "ó")
        tags = tags.replace("&Oacute;", "Ó")
        track = Track(title=form.title.data, lyrics=tags, lyrics_with_scraps=tags, author=current_user,
                      date_release=form.date_release.data, lyrics_by=form.lyrics_by.data,
                      description=form.description.data)

        for cd in albums_list:
            album = Album.query.filter_by(id=int(cd)).first_or_404()

            track.albums.append(album)
        db.session.add(track)
        db.session.commit()

        db.session.commit()
        flash("Utwór został dodany", "success")
        return redirect(url_for('user_activity.tracks'))

    return render_template('create_track.html', title="Nowy Utwór", albums=albums,
                           legend="Dodaj nowy utwór", form=form, image_file=check_image())


@user_activity.route('/track/<int:track_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_track(track_id):
    track = Track.query.get_or_404(track_id)
    albums = Album.query.all()
    if track.author != current_user:
        abort(403)
    form = TrackForm()
    if form.validate_on_submit():
        albums_list = request.form.getlist("albums")
        tags = form.lyrics.data
        tags = tags.replace("<p>", '')
        tags = tags.replace("</p>", "<br/>")

        track.title = form.title.data
        track.lyrics = tags
        track.lyrics_with_scraps = tags
        track.description = form.description.data
        track.date_release = form.date_release.data
        track.lyrics_by = form.lyrics_by.data
        track.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        for cd in albums_list:
            album = Album.query.filter_by(id=int(cd)).first_or_404()

            track.albums.append(album)
        for scrap in track.scraps:
            for opinion in scrap.opinions:
                db.session.delete(opinion)
            for rate in scrap.rates:
                db.session.delete(rate)
            db.session.delete(scrap)
        db.session.commit()
        flash("Utwór zaktualizowany!", 'success')
        return redirect(url_for('user_activity.track', track_id=track.id))
    elif request.method == "GET":
        form.title.data = track.title
        form.lyrics.data = track.lyrics
        form.description.data = track.description
        form.date_release.data = track.date_release
        form.lyrics_by.data = track.lyrics_by
    return render_template('create_track.html', title="Edytuj utwór", track_id=track_id,
                           legend="Edytuj utwór", form=form, image_file=check_image(), albums=albums,
                           track_albums=track.albums)


@user_activity.route('/track/<int:track_id>/delete', methods=['POST'])
@login_my_required
def delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    if track.author != current_user and not current_user.is_admin:
        abort(403)
    scr_len = len(track.scraps)
    int_len = len(track.interpretations)
    posts_len = len(track.comments)
    trans_len = len(track.translations)
    any_length = bool()
    if scr_len > 0 or int_len > 0 or posts_len > 0 or trans_len > 0:
        any_length = True

    if not current_user.is_admin and any_length:
        to_admin_delete('track', track_id)
        return redirect(url_for('user_activity.track', track_id=track.id))
    elif current_user.is_admin and any_length:
        clear_track(track)
        db.session.delete(track)
        db.session.commit()
    elif not any_length:
        db.session.delete(track)
        db.session.commit()
    flash("Utwór został usunięty", 'success')
    return redirect(url_for('user_activity.tracks'))


@user_activity.route('/track/<int:track_id>/reply', methods=['GET', 'POST'])
@login_my_required
def track_reply(track_id):
    form = PostForm()
    if form.validate_on_submit():
        post = Track_Post(reply=form.reply.data, author=current_user, track_id=track_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.track', track_id=track_id))
    return render_template('track_reply.html', title="Dodaj Opinię",
                           legend="Odpowiedz", form=form, image_file=check_image(),
                           track_id=track_id, reply_id=None)


@user_activity.route('/track/<int:track_id>/reply_to/<int:post_id>', methods=['GET', 'POST'])
@login_my_required
def quote_track_post(track_id, post_id):
    post = Track_Post.query.get_or_404(post_id)
    form = PostForm()
    date_posted = str(datetime.strptime(str(post.date_posted), "%Y-%m-%d %H:%M:%S.%f"))
    date_posted = date_posted.split(".")[0]
    quote = "<div>" \
            "<div style='background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;'>" \
            "<b>" + post.author.username + "</b> powiedział " + date_posted + \
            "</div>" \
            "<blockquote class='cke_contents_ltr blockquote'>" + post.reply + "</blockquote>" \
                                                                              "<p></p></div>"
    if form.validate_on_submit():
        post = Track_Post(reply=form.reply.data, author=current_user, track_id=track_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.track', track_id=track_id))
    elif request.method == "GET":
        form.reply.data = Markup(quote)
    return render_template('track_reply.html', title="Rozwiń wątek",
                           legend="Odpowiedz użytkownikowi " + post.author.username, form=form,
                           image_file=check_image(),
                           track_id=track_id, reply_id=None)


@user_activity.route('/track/<int:track_id>/reply/<int:post_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_track_post(post_id, track_id):
    track = Track.query.get_or_404(track_id)
    post = Track_Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.reply = form.reply.data
        post.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Odpowiedź została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.track', track_id=track.id))
    elif request.method == "GET":
        form.reply.data = post.reply
    return render_template('track_reply.html', title="Edytuj odpowiedź",
                           legend="Edytuj odpowiedź", form=form,
                           image_file=check_image(), track_id=track.id)


@user_activity.route('/track/<int:track_id>/reply/<int:post_id>/delete', methods=['POST'])
@login_my_required
def delete_track_post(track_id, post_id):
    track = Track.query.get_or_404(track_id)
    post = Track_Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Odpowiedź została usunięta", 'success')
    return redirect(url_for('user_activity.track', track_id=track.id))


@user_activity.route('/track/<int:track_id>/scraps', methods=['GET', 'POST'])
@login_my_required
def scraps(track_id):
    track = Track.query.get_or_404(track_id)
    tags = track.lyrics_with_scraps
    scrap_descriptions = []
    scrap_rates_up = []
    scrap_rates_down = []
    scrap_authors = []
    opinions = []
    scrap_authors_raw = []
    last_id = Scrap.query. \
        order_by(desc(Scrap.id)).first()
    '''print("_____________________________________________________-", file=sys.stderr)
    print(last_id, file=sys.stderr)
    print("_____________________________________________________", file=sys.stderr)'''
    if last_id is not None:
        last_id = json.dumps(last_id.id)
    else:
        last_id = json.dumps(0)
    for scrap in track.scraps:
        id = scrap.id

        pluses = Scrap_Rating.query.filter_by(scrap_id=id, rate='1').count()
        minuses = Scrap_Rating.query.filter_by(scrap_id=id, rate='0').count()
        scrap_rates_up.append({'id': id, 'rates': pluses})
        scrap_rates_down.append({'id': id, 'rates': minuses})

        scrap_descriptions.append({'id': id, 'description': scrap.description})

        scrap_author = {}
        scrap_author['id'] = id
        scrap_author['author'] = scrap.author.username
        scrap_author['is_published'] = scrap.published
        scrap_authors.append(scrap_author)

        scrap_authors_raw.append({'id': id, 'author': scrap.author, 'is_published': scrap.published})

        for opinion in scrap.opinions:
            opinions.append(opinion)

    scrap_descriptions = json.dumps(scrap_descriptions)
    scrap_authors = json.dumps(scrap_authors)
    scrap_rates_up = json.dumps(scrap_rates_up)
    scrap_rates_down = json.dumps(scrap_rates_down)
    tags = Markup(tags)
    form = ScrapForm()
    comment_form = CommentForm()
    if form.validate_on_submit():
        if track.lyrics_with_scraps == form.lyrics_with_scraps.data:
            flash("Oznaczono błędny fragment", "danger")
            return redirect(url_for('user_activity.scraps', track_id=track_id))
        else:
            lyrics_with_scraps = form.lyrics_with_scraps.data
            lyrics_with_scraps = lyrics_with_scraps.replace(
                '<div id="darkLayer" class="darkClass" style="display: block;"></div>', '')
            track.lyrics_with_scraps = lyrics_with_scraps
            new_scrap = Scrap(description=form.description.data, track_id=track_id,
                              author=current_user)
            db.session.add(new_scrap)
            db.session.commit()
            flash("Fragment został oznaczony", "success")
            return redirect(url_for('user_activity.scraps', track_id=track_id))

    return render_template('scraps.html', title=track.title, image_file=check_image(), track=track, tags=tags,
                           last_id=last_id,
                           scrap_rates_up=scrap_rates_up, scrap_rates_down=scrap_rates_down, form=form,
                           scrap_descriptions=scrap_descriptions,
                           scrap_authors=scrap_authors, comment_form=comment_form, opinions=opinions,
                           scrap_authors_raw=scrap_authors_raw)


@user_activity.route('/scrap/<int:scrap_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_scrap(scrap_id):
    scrap = Scrap.query.get_or_404(scrap_id)
    if scrap.author != current_user:
        abort(403)
    form = OpinionForm()
    if form.validate_on_submit():
        scrap.description = form.reply.data
        scrap.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Opis został zaktualizowany!", 'success')
        return redirect(url_for('user_activity.scraps', track_id=scrap.track_id))
    elif request.method == "GET":
        form.reply.data = scrap.description
    return render_template('opinion_reply.html', title="Edytuj fragment",
                           legend="Edytuj fragment", form=form,
                           image_file=check_image(), scrap_id=scrap.id, track_id=scrap.track_id)


@user_activity.route('/scrap/<int:scrap_id>/delete', methods=['POST'])
@login_my_required
def delete_scrap(scrap_id):
    scrap = Scrap.query.get_or_404(scrap_id)
    if scrap.author != current_user and not current_user.is_admin:
        abort(403)

    lyrics = request.form.get('scrap_delete_lyrics')
    print("_____________________________________________________-", file=sys.stderr)
    print(lyrics, file=sys.stderr)
    print("_____________________________________________________", file=sys.stderr)

    scrap.track.lyrics_with_scraps = lyrics
    clear_target(scrap)
    db.session.delete(scrap)
    db.session.commit()

    flash("Fragment został usunięty", 'success')
    return redirect(url_for('user_activity.scraps', scrap_id=scrap_id, track_id=scrap.track_id))


@user_activity.route('/track/<int:track_id>/interpretations', methods=['GET', 'POST'])
@login_my_required
def interpretations(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    interpretations = Interpretation.query. \
        filter_by(track=track). \
        order_by(asc(Interpretation.date_posted))
    rates_up = {}
    rates_down = {}
    for interpretation in track.interpretations:
        pluses = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='1').count()
        minuses = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='0').count()

        rates_up[interpretation.id] = [pluses]
        rates_down[interpretation.id] = [minuses]

    return render_template('interpretations.html', title=track.title, image_file=check_image(),
                           track=track, tags=tags, interpretations=interpretations, rates_up=rates_up,
                           rates_down=rates_down)


@user_activity.route('/track/<int:track_id>/interpretation/<int:interpretation_id>', methods=['GET', 'POST'])
@login_my_required
def interpretation(track_id, interpretation_id):
    track = Track.query.get_or_404(track_id)
    interpretation = Interpretation.query.get_or_404(interpretation_id)
    tags = Markup(track.lyrics)
    interpretation_text = Markup(interpretation.text)
    opinions = []
    for opinion in interpretation.opinions:
        opinions.append(Markup(opinion.text))
    pluses = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='1').count()
    minuses = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='0').count()
    been_rated_up = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='1',
                                                          user_id=current_user.id).first()
    been_rated_down = Interpretation_Rating.query.filter_by(interpretation_id=interpretation.id, rate='0',
                                                            user_id=current_user.id).first()
    if been_rated_up is not None:
        rate_author = "my_rate_up"
    elif been_rated_down is not None:
        rate_author = "my_rate_down"
    else:
        rate_author = "else"
    rates_up = [pluses, rate_author]
    rates_down = [minuses, rate_author]
    return render_template('interpretation.html', title=track.title, image_file=check_image(), opinions=opinions,
                           track=track, tags=tags, interpretation=interpretation,
                           interpretation_text=interpretation_text, rates_up=rates_up, rates_down=rates_down)


@user_activity.route('/track/<int:track_id>/interpretation/new', methods=['GET', 'POST'])
@login_my_required
def new_interpretation(track_id):
    form = InterpretationForm()
    if form.validate_on_submit():
        interpretation = Interpretation(title=form.title.data, text=form.text.data, author=current_user,
                                        track_id=track_id)
        db.session.add(interpretation)
        db.session.commit()
        flash("Interpretacja została dodana", "success")
        return redirect(url_for('user_activity.interpretations', track_id=track_id))
    return render_template('create_interpretation.html', title="Dodaj interpretacje",
                           legend="Zaproponuj swoją interpretację", form=form, image_file=check_image())


@user_activity.route('/track/<int:track_id>/interpretation/<int:interpretation_id>/delete', methods=['POST'])
@login_my_required
def delete_interpretation(track_id, interpretation_id):
    interpretation = Interpretation.query.get_or_404(interpretation_id)
    if interpretation.author != current_user and not current_user.is_admin:
        abort(403)
    rate_len = len(interpretation.rates)
    op_len = len(interpretation.opinions)
    all_length = False
    if rate_len > 0 or op_len > 0:
        all_length = True
    if not current_user.is_admin and all_length:
        to_admin_delete('interpretation', interpretation_id)
        return redirect(url_for('user_activity.interpretation', track_id=track_id, interpretation_id=interpretation.id))
    elif current_user.is_admin and all_length:
        clear_target(interpretation)
        db.session.delete(interpretation)
        db.session.commit()
    elif not all_length:
        db.session.delete(interpretation)
        db.session.commit()
    flash("Interpretacja została usunięta", 'success')
    return redirect(url_for('user_activity.interpretations', track_id=track_id))


@user_activity.route('/track/<int:track_id>/update/<int:interpretation_id>/update', methods=['GET', 'POST'])
@login_required
def update_interpretation(track_id, interpretation_id):
    interpretation = Interpretation.query.get_or_404(interpretation_id)
    if interpretation.author != current_user:
        abort(403)
    form = InterpretationForm()
    if form.validate_on_submit():
        interpretation.title = form.title.data
        interpretation.text = form.text.data
        interpretation.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Interpretacja została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.interpretation', track_id=track_id, interpretation_id=interpretation_id))
    elif request.method == "GET":
        form.title.data = interpretation.title
        form.text.data = interpretation.text
    return render_template('create_interpretation.html', title="Edytuj interpretację",
                           legend="Edytuj interpretację", form=form,
                           image_file=check_image(), track_id=track_id, interpretation_id=interpretation_id)


@user_activity.route('/track/<int:track_id>/interpretation/<int:interpretation_id>/reply', methods=['GET', 'POST'])
@login_my_required
def interpretation_reply(track_id, interpretation_id):
    form = OpinionForm()
    if form.validate_on_submit():
        new_opinion = Interpretation_Opinion(text=form.reply.data, author=current_user,
                                             interpretation_id=interpretation_id)
        db.session.add(new_opinion)
        db.session.commit()
        flash("Opinia została dodana", "success")
        return redirect(url_for('user_activity.interpretation', track_id=track_id, interpretation_id=interpretation_id))
    return render_template('opinion_reply.html', title="Wyraź swoją opinię",
                           legend="Opinia", form=form, image_file=check_image(),
                           track_id=track_id, interpretation_id=interpretation_id, reply_id=None)


@user_activity.route(
    '/track/<int:track_id>/interpretation/<int:interpretation_id>/reply_to/<int:interpretation_opinion_id>',
    methods=['GET', 'POST'])
@login_my_required
def quote_interpretation_reply(track_id, interpretation_opinion_id, interpretation_id):
    interpretation_opinion = Interpretation_Opinion.query.get_or_404(interpretation_opinion_id)
    form = OpinionForm()
    date_posted = str(datetime.strptime(str(interpretation_opinion.date_posted), "%Y-%m-%d %H:%M:%S.%f"))
    date_posted = date_posted.split(".")[0]
    quote = "<div>" \
            "<div style='background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;'>" \
            "<b>" + interpretation_opinion.author.username + "</b> powiedział " + date_posted + \
            "</div>" \
            "<blockquote class='cke_contents_ltr blockquote'>" + interpretation_opinion.text + "</blockquote>" \
                                                                                               "<p></p></div>"
    if form.validate_on_submit():
        new_opinion = Interpretation_Opinion(text=form.reply.data, author=current_user,
                                             interpretation_id=interpretation_id)
        db.session.add(new_opinion)
        db.session.commit()
        flash("Opinia została dodana", "success")
        return redirect(url_for('user_activity.interpretation', track_id=track_id, interpretation_id=interpretation_id))
    elif request.method == "GET":
        form.reply.data = Markup(quote)
    return render_template('opinion_reply.html', title="Wyraź swoją opinię",
                           legend="Odpowiedz użytkownikowi " + interpretation_opinion.author.username, form=form,
                           image_file=check_image(), interpretation_opinion_id=interpretation_opinion_id,
                           track_id=track_id, interpretation_id=interpretation_id, reply_id=None)


@user_activity.route(
    '/track/<int:track_id>/interpretation/<int:interpretation_id>/opinion/<int:interpretation_opinion_id>/update',
    methods=['GET', 'POST'])
@login_my_required
def update_interpretation_opinion(track_id, interpretation_id, interpretation_opinion_id):
    interpretation_opinion = Interpretation_Opinion.query.get_or_404(interpretation_opinion_id)
    if interpretation_opinion.author != current_user:
        abort(403)
    form = OpinionForm()
    if form.validate_on_submit():
        interpretation_opinion.text = form.reply.data
        interpretation.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Opinia została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.interpretation', track_id=track_id, interpretation_id=interpretation_id))
    elif request.method == "GET":
        form.reply.data = interpretation_opinion.text
    return render_template('opinion_reply.html', title="Edytuj opinię",
                           legend="Edytuj opinię", form=form, interpretation_opinion_id=interpretation_opinion_id,
                           image_file=check_image(), track_id=track_id, interpretation_id=interpretation_id)


@user_activity.route(
    '/scrap_opinion/<int:scrap_opinion_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_scrap_opinion(scrap_opinion_id):
    scrap_opinion = Scrap_Opinion.query.get_or_404(scrap_opinion_id)
    if scrap_opinion.author != current_user:
        abort(403)
    form = OpinionForm()
    if form.validate_on_submit():
        tags = form.reply.data
        tags = tags.replace("<p>", '')
        tags = tags.replace("</p>", '')
        scrap_opinion.text = tags
        interpretation.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Opinia została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.scraps', track_id=scrap_opinion.scrap.track_id))
    elif request.method == "GET":
        form.reply.data = scrap_opinion.text
    return render_template('opinion_reply.html', title="Edytuj opinię",
                           legend="Edytuj opinię", form=form, track_id=scrap_opinion.scrap.track_id,
                           scrap_opinion_id=scrap_opinion_id, image_file=check_image())


@user_activity.route(
    '/scrap_opinion/<int:scrap_opinion_id>/delete', methods=['POST'])
@login_my_required
def delete_scrap_opinion(scrap_opinion_id):
    scrap_opinion = Scrap_Opinion.query.get_or_404(scrap_opinion_id)
    track_id = scrap_opinion.scrap.track_id
    if scrap_opinion.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(scrap_opinion)
    db.session.commit()
    flash("Opinia została usunięta", 'success')
    return redirect(url_for('user_activity.scraps', track_id=track_id))


@user_activity.route(
    '/track/<int:track_id>/interpretation/<int:interpretation_id>/opinion/<int:interpretation_opinion_id>/delete',
    methods=['POST'])
@login_my_required
def delete_interpretation_opinion(track_id, interpretation_id, interpretation_opinion_id):
    interpretation_opinion = Interpretation_Opinion.query.get_or_404(interpretation_opinion_id)
    if interpretation_opinion.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(interpretation_opinion)
    db.session.commit()
    flash("Opinia została usunięta", 'success')
    return redirect(url_for('user_activity.interpretation', interpretation_id=interpretation_id, track_id=track_id))


@user_activity.route('/track/<int:track_id>/translations', methods=['GET', 'POST'])
@login_my_required
def translations(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    rates_up = {}
    rates_down = {}
    for translation in track.translations:
        pluses = Translation_Rating.query.filter_by(translation_id=translation.id, rate='1').count()
        minuses = Translation_Rating.query.filter_by(translation_id=translation.id, rate='0').count()

        rates_up[translation.id] = [pluses]
        rates_down[translation.id] = [minuses]

    translations = Translation.query. \
        filter_by(track=track). \
        order_by(asc(Translation.date_posted))

    return render_template('translations.html', title=track.title, image_file=check_image(),
                           track=track, tags=tags, translations=translations, rates_down=rates_down, rates_up=rates_up)


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>', methods=['GET', 'POST'])
@login_my_required
def translation(track_id, translation_id):
    track = Track.query.get_or_404(track_id)
    translation = Translation.query.get_or_404(translation_id)
    tags = Markup(track.lyrics)
    translation_text = Markup(translation.lyrics_trans)
    opinions = []
    for opinion in translation.opinions:
        opinions.append(Markup(opinion.text))

    pluses = Translation_Rating.query.filter_by(translation_id=translation.id, rate='1').count()
    minuses = Translation_Rating.query.filter_by(translation_id=translation.id, rate='0').count()
    been_rated_up = Translation_Rating.query.filter_by(translation_id=translation.id, rate='1',
                                                       user_id=current_user.id).first()
    been_rated_down = Translation_Rating.query.filter_by(translation_id=translation.id, rate='0',
                                                         user_id=current_user.id).first()
    if been_rated_up is not None:
        rate_author = "my_rate_up"
    elif been_rated_down is not None:
        rate_author = "my_rate_down"
    else:
        rate_author = "else"
    rates_up = [pluses, rate_author]
    rates_down = [minuses, rate_author]
    return render_template('translation.html', title=track.title, image_file=check_image(), opinions=opinions,
                           track=track, tags=tags, rates_up=rates_up, rates_down=rates_down, translation=translation,
                           translation_text=translation_text)


@user_activity.route('/track/<int:track_id>/translation/new', methods=['GET', 'POST'])
@login_my_required
def new_translation(track_id):
    form = TranslationForm()
    if form.validate_on_submit():
        translation = Translation(title=form.title.data, lyrics_trans=form.text.data, author=current_user,
                                  track_id=track_id)
        db.session.add(translation)
        db.session.commit()
        flash("Tłumaczenie zostało dodana", "success")
        return redirect(url_for('user_activity.translations', track_id=track_id))
    return render_template('create_translation.html', title="Dodaj tłumaczenie",
                           legend="Zaproponuj swoje tłumaczenie", form=form, image_file=check_image())


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>/delete', methods=['POST'])
@login_my_required
def delete_translation(track_id, translation_id):
    translation = Translation.query.get_or_404(translation_id)
    if translation.author != current_user and not current_user.is_admin:
        abort(403)
    rate_len = len(translation.rates)
    op_len = len(translation.opinions)
    all_length = False
    if rate_len > 0 or op_len > 0:
        all_length = True
    if not current_user.is_admin and all_length:
        to_admin_delete('translation', translation_id)
        return redirect(url_for('user_activity.translation', track_id=track_id, translation_id=translation_id))
    elif current_user.is_admin and all_length:
        clear_target(translation)
        db.session.delete(translation)
        db.session.commit()
    elif not all_length:
        db.session.delete(translation)
        db.session.commit()
    flash("Tłumaczenie zostało usunięte", 'success')
    return redirect(url_for('user_activity.translations', track_id=track_id))


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>/update', methods=['GET', 'POST'])
@login_my_required
def update_translation(track_id, translation_id):
    translation = Translation.query.get_or_404(translation_id)
    if translation.author != current_user:
        abort(403)
    form = TranslationForm()
    if form.validate_on_submit():
        translation.title = form.title.data
        translation.lyrics_trans = form.text.data
        translation.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Interpretacja została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.translation', track_id=track_id, translation_id=translation_id))
    elif request.method == "GET":
        form.title.data = translation.title
        form.text.data = translation.lyrics_trans
    return render_template('create_translation.html', title="Edytuj interpretację",
                           legend="Edytuj interpretację", form=form,
                           image_file=check_image(), track_id=track_id, translation_id=translation_id)


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>/reply', methods=['GET', 'POST'])
@login_my_required
def translation_reply(track_id, translation_id):
    form = OpinionForm()
    if form.validate_on_submit():
        new_opinion = Translation_Opinion(text=form.reply.data, author=current_user, translation_id=translation_id)
        db.session.add(new_opinion)
        db.session.commit()
        flash("Opinia została dodana", "success")
        return redirect(url_for('user_activity.translation', track_id=track_id, translation_id=translation_id))
    return render_template('opinion_reply.html', title="Wyraź swoją opinię",
                           legend="Opinia", form=form, image_file=check_image(),
                           track_id=track_id, translation_id=translation_id, reply_id=None)


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>/reply_to/<int:translation_opinion_id>',
                     methods=['GET', 'POST'])
@login_my_required
def quote_translation_reply(track_id, translation_opinion_id, translation_id):
    translation_opinion = Translation_Opinion.query.get_or_404(translation_opinion_id)
    form = OpinionForm()
    date_posted = str(datetime.strptime(str(translation_opinion.date_posted), "%Y-%m-%d %H:%M:%S.%f"))
    date_posted = date_posted.split(".")[0]
    quote = "<div>" \
            "<div style='background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;'>" \
            "<b>" + translation_opinion.author.username + "</b> powiedział " + date_posted + \
            "</div>" \
            "<blockquote class='cke_contents_ltr blockquote'>" + translation_opinion.text + "</blockquote>" \
                                                                                            "<p></p></div>"
    if form.validate_on_submit():
        new_opinion = Translation_Opinion(text=form.reply.data, author=current_user, translation_id=translation_id)
        db.session.add(new_opinion)
        db.session.commit()
        flash("Opinia została dodana", "success")
        return redirect(url_for('user_activity.translation', track_id=track_id, translation_id=translation_id))
    elif request.method == "GET":
        form.reply.data = Markup(quote)
    return render_template('opinion_reply.html', title="Wyraź swoją opinię",
                           legend="Odpowiedz użytkownikowi " + translation_opinion.author.username, form=form,
                           image_file=check_image(), translation_opinion_id=translation_opinion_id,
                           track_id=track_id, translation_id=translation_id, reply_id=None)


@user_activity.route(
    '/track/<int:track_id>/translation/<int:translation_id>/opinion/<int:translation_opinion_id>/update',
    methods=['GET', 'POST'])
@login_my_required
def update_translation_opinion(track_id, translation_id, translation_opinion_id):
    translation_opinion = Translation_Opinion.query.get_or_404(translation_opinion_id)
    if translation_opinion.author != current_user:
        abort(403)
    form = OpinionForm()
    if form.validate_on_submit():
        translation_opinion.text = form.reply.data
        translation.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Opinia została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.translation', track_id=track_id, translation_id=translation_id))
    elif request.method == "GET":
        form.reply.data = translation_opinion.text
    return render_template('opinion_reply.html', title="Edytuj opinię",
                           legend="Edytuj opinię", form=form, translation_opinion_id=translation_opinion_id,
                           image_file=check_image(), track_id=track_id, translation_id=translation_id)


@user_activity.route(
    '/track/<int:track_id>/translation/<int:translation_id>/opinion/<int:translation_opinion_id>/delete',
    methods=['POST'])
@login_my_required
def delete_translation_opinion(track_id, translation_id, translation_opinion_id):
    translation_opinion = Translation_Opinion.query.get_or_404(translation_opinion_id)
    if translation_opinion.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(translation_opinion)
    db.session.commit()
    flash("Opinia została usunięta", 'success')
    return redirect(url_for('user_activity.translation', translation_id=translation_id, track_id=track_id))


@user_activity.route('/track/<int:track_id>/scrap/comment', methods=['POST'])
@login_my_required
def add_scrap_comment(track_id):
    if request.method == 'POST':
        form = request.form
        scrap_id = form['scrap_to_comment']
        scrap = Scrap.query.get_or_404(scrap_id)
        track = Track.query.get_or_404(track_id)
        if scrap not in track.scraps:
            abort(403)
        add_scrap_comment = Scrap_Opinion(text=form['reply'], scrap_id=scrap_id, author=current_user)
        db.session.add(add_scrap_comment)
        flash("Komentarz został dodany", 'success')
        db.session.commit()
        return redirect(url_for('user_activity.scraps', track_id=track_id))


@user_activity.route('/track/<int:track_id>/scrap/rate', methods=['POST'])
@login_my_required
def rate_scrap(track_id):
    if request.method == 'POST':
        form = request.form
        scrap_id = form['scrap_to_rate']
        scrap = Scrap.query.get_or_404(scrap_id)
        track = Track.query.get_or_404(track_id)
        if scrap not in track.scraps:
            abort(403)
        old_rating = Scrap_Rating.query.filter_by(user_id=current_user.id, scrap_id=scrap_id).first()
        if old_rating is not None:
            if old_rating.rate == '1' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '1' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                rate = 0
                rate_update = Scrap_Rating(rate=rate, scrap_id=scrap_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
            elif old_rating.rate == '0' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '0' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                rate = 1
                rate_update = Scrap_Rating(rate=rate, scrap_id=scrap_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
        else:
            if form["rate_btn"] == "plus":
                rate = 1
            elif form["rate_btn"] == "minus":
                rate = 0
            rate_update = Scrap_Rating(rate=rate, scrap_id=scrap_id, author=current_user)
            db.session.add(rate_update)
            flash("Ocena została dodana", 'success')
        db.session.commit()
        return redirect(url_for('user_activity.scraps', track_id=track_id))


@user_activity.route('/track/<int:track_id>/translation/<int:translation_id>/rate', methods=['POST'])
@login_my_required
def rate_translation(track_id, translation_id):
    if request.method == 'POST':
        form = request.form
        translation_id = translation_id
        translation = Translation.query.get_or_404(translation_id)
        track = Track.query.get_or_404(track_id)
        if translation not in track.translations:
            abort(403)
        old_rating = Translation_Rating.query.filter_by(user_id=current_user.id, translation_id=translation_id).first()
        if old_rating is not None:
            if old_rating.rate == '1' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '1' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                rate = 0
                rate_update = Translation_Rating(rate=rate, translation_id=translation_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
            elif old_rating.rate == '0' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '0' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                rate = 1
                rate_update = Translation_Rating(rate=rate, translation_id=translation_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
        else:
            if form["rate_btn"] == "plus":
                rate = 1
            elif form["rate_btn"] == "minus":
                rate = 0
            rate_update = Translation_Rating(rate=rate, translation_id=translation_id, author=current_user)
            db.session.add(rate_update)
            flash("Ocena została dodana", 'success')
        db.session.commit()
        return redirect(url_for('user_activity.translation', translation_id=translation_id, track_id=track_id))


@user_activity.route('/track/<int:track_id>/interpretation/<int:interpretation_id>/rate', methods=['POST'])
@login_my_required
def rate_interpretation(track_id, interpretation_id):
    if request.method == 'POST':
        form = request.form
        interpretation_id = interpretation_id
        interpretation = Interpretation.query.get_or_404(interpretation_id)
        track = Track.query.get_or_404(track_id)
        if interpretation not in track.interpretations:
            abort(403)
        old_rating = Interpretation_Rating.query.filter_by(user_id=current_user.id,
                                                           interpretation_id=interpretation_id).first()
        if old_rating is not None:
            if old_rating.rate == '1' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '1' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                rate = 0
                rate_update = Interpretation_Rating(rate=rate, interpretation_id=interpretation_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
            elif old_rating.rate == '0' and form["rate_btn"] == "minus":
                db.session.delete(old_rating)
                flash("Usunięto ocenę", 'warning')
            elif old_rating.rate == '0' and form["rate_btn"] == "plus":
                db.session.delete(old_rating)
                rate = 1
                rate_update = Interpretation_Rating(rate=rate, interpretation_id=interpretation_id, author=current_user)
                db.session.add(rate_update)
                flash("Zmieniono ocenę", 'success')
        else:
            if form["rate_btn"] == "plus":
                rate = 1
            elif form["rate_btn"] == "minus":
                rate = 0
            rate_update = Interpretation_Rating(rate=rate, interpretation_id=interpretation_id, author=current_user)
            db.session.add(rate_update)
            flash("Ocena została dodana", 'success')
        db.session.commit()
        return redirect(url_for('user_activity.interpretation', interpretation_id=interpretation_id, track_id=track_id))


@user_activity.route("/user/activity/<string:username>")
@login_my_required
def user_actions(username):
    user = User.query.filter_by(username=username).first_or_404()
    activity = {}
    activity['threads'] = Thread.query. \
        filter_by(author=user). \
        order_by(desc(Thread.date_posted)).all()
    activity['tracks'] = Track.query. \
        filter_by(author=user). \
        order_by(desc(Track.date_posted)).all()
    activity['scraps'] = Scrap.query. \
        filter_by(author=user). \
        order_by(desc(Scrap.date_posted)).all()
    activity['translations'] = Translation.query. \
        filter_by(author=user). \
        order_by(desc(Translation.date_posted)).all()
    activity['interpretations'] = Interpretation.query. \
        filter_by(author=user). \
        order_by(desc(Interpretation.date_posted)).all()

    return render_template('user_activity.html', title="Aktywność użytkownika", image_file=check_image(),
                           activity=activity, user=user)

