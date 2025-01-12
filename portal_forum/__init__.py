from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from portal_forum.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "Zaloguj się aby uzyskać dostęp do strony"
login_manager.login_message_category = 'info'





def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from portal_forum.users.routes import users
    from portal_forum.user_activity.routes import user_activity
    from portal_forum.main.routes import main
    app.register_blueprint(users)
    app.register_blueprint(user_activity)
    app.register_blueprint(main)

    return app





