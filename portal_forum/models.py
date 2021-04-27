
from portal_forum import db, login_manager
from datetime import datetime
from flask_login import UserMixin #autentykacja w sesji

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False)
    threads = db.relationship('Thread', backref='author', lazy=True)
    tracks = db.relationship('Track', backref='author', lazy=True)
    thread_posts = db.relationship('Thread_Post', backref='author', lazy=True)
    track_post = db.relationship('Track_Post', backref='author', lazy=True)
    scrap = db.relationship('Scrap', backref='author', lazy=True)
    scrap_Opinion = db.relationship('Scrap_Opinion', backref='author', lazy=True)
    translation = db.relationship('Translation', backref='author', lazy=True)
    translation_Opinion = db.relationship('Translation_Opinion', backref='author', lazy=True)
    #discussion_Post = db.relationship('Discussion_Post', backref='author', lazy=True)
    interpretation = db.relationship('Interpretation', backref='author', lazy=True)
    interpretation_Post = db.relationship('Interpretation_Opinion', backref='author', lazy=True)
    scrap_rates = db.relationship('Scrap_Rating', backref='author', lazy=True)
    interpretation_rates = db.relationship('Interpretation_Rating', backref='author', lazy=True)
    translation_rates = db.relationship('Translation_Rating', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(128), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    threads = db.relationship('Thread_Post', backref='thread', lazy=True)

    def __repr__(self):
        return f"Thread('{self.date_posted}', '{self.topic}')"

class Thread_Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reply = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)

    def __repr__(self):
        return f"Thread_Post('{self.id}','{self.date_posted}')"

TrackAlbums = db.Table('track_albums',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('album_id', db.Integer, db.ForeignKey('album.id')))

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    date_release = db.Column(db.SmallInteger, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    description = db.Column(db.Text, nullable=True)
    tracks = db.relationship(
        "Track",
        secondary=TrackAlbums,
        back_populates="albums",
        cascade="all, delete",
    )

    def __repr__(self):
        return f"Album('{self.title}', '{self.date_release}')"

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    date_release = db.Column(db.SmallInteger, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lyrics = db.Column(db.Text, nullable=False)
    lyrics_with_scraps = db.Column(db.Text, nullable=False)
    lyrics_by = db.Column(db.String(128), nullable=True)
    published = db.Column(db.SmallInteger, default=0, nullable=False)
    description = db.Column(db.Text, nullable=True)
    albums = db.relationship(
        "Album",
        secondary=TrackAlbums,
        back_populates="tracks",
        passive_deletes=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scraps = db.relationship('Scrap', backref='track', lazy=True)
    translations = db.relationship('Translation', backref='track', lazy=True)
    comments = db.relationship('Track_Post', backref='track', lazy=True)
    interpretations = db.relationship('Interpretation', backref='track', lazy=True)

    def __repr__(self):
        return f"Track('{self.title}', '{self.date_release}')"
'''
class TrackAlbums(db.Model):
    __tablename__ = 'track_albums'
    id = db.Column(db.Integer(), primary_key=True)
    album_id = db.Column(db.Integer(), db.ForeignKey('album.id', ondelete='CASCADE'))
    track_id = db.Column(db.Integer(), db.ForeignKey('track.id', ondelete='CASCADE'))
    def __repr__(self):
        return f"track_albums('{self.album}','{self.track_id}')"
'''

class Track_Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reply = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)

    def __repr__(self):
        return f"Track_Post('{self.id}', '{self.date_posted}')"


class Scrap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    '''index_from = db.Column(db.Integer, nullable=False)
    index_to = db.Column(db.Integer, nullable=False)'''
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    opinions = db.relationship('Scrap_Opinion', backref='scrap', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rates = db.relationship('Scrap_Rating', backref='scrap', lazy=True)
    published = db.Column(db.SmallInteger, default=0, nullable=False)

    def __repr__(self):
        return f"Scrap('{self.description}')"

class Scrap_Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    scrap_id = db.Column(db.Integer, db.ForeignKey('scrap.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Scrap_Opinion('{self.scrap_id}', '{self.text}')"

class Scrap_Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.String(1), nullable=False)
    scrap_id = db.Column(db.Integer, db.ForeignKey('scrap.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Scrap_Rating('{self.scrap_id}'"

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    lyrics_trans = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    opinions = db.relationship('Translation_Opinion', backref='translation', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rates = db.relationship('Translation_Rating', backref='translation', lazy=True)
    published = db.Column(db.SmallInteger, default=0, nullable=False)

    def __repr__(self):
        return f"Translation('{self.lyrics_trans}')"

class Translation_Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    translation_id = db.Column(db.Integer, db.ForeignKey('translation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Translation_Opinion('{self.translation_id}', '{self.text}')"

class Translation_Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.String(1), nullable=False)
    translation_id = db.Column(db.Integer, db.ForeignKey('translation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Scrap_Rating('{self.scrap_id}', '{self.rate}')"

'''
class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    posts = db.relationship('Discussion_Post', backref='discussion', lazy=True)

    def __repr__(self):
        return f"Discussion('{self.id}', '{self.track_id}')"

class Discussion_Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=True)
    reply = db.Column(db.Text, nullable=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Discussion_Post('{self.discussion_id}', '{self.text}')"
'''

class Interpretation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    text = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    opinions = db.relationship('Interpretation_Opinion', backref='interpretation', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rates = db.relationship('Interpretation_Rating', backref='interpretation', lazy=True)
    published = db.Column(db.SmallInteger, default=0, nullable=False)

    def __repr__(self):
        return f"Interpretation"

class Interpretation_Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    interpretation_id = db.Column(db.Integer, db.ForeignKey('interpretation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Interpretation_Opinion"

class Interpretation_Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.String(1), nullable=False)
    interpretation_id = db.Column(db.Integer, db.ForeignKey('interpretation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Scrap_Rating('{self.scrap_id}', '{self.rate}')"

class To_Delete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"target to delete('{self.target_id}', '{self.type}')"