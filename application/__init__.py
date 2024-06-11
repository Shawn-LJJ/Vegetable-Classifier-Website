from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import getConfig

# instantiate database and the flask login
db = SQLAlchemy()
login_manager = LoginManager()

# function to make the app, also takes in which config
def create_app(config):

    # instantiate app
    app = Flask(__name__)
    app.config.from_object(getConfig(config))  # get config

    # set up the db
    with app.app_context():
        db.init_app(app)
        from .models import User, History
        db.create_all()
        db.session.commit()
    
    # and then the login manager
    login_manager.init_app(app)
    # while also set the user loader, as specified in their docs
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter(User.id == int(user_id)).first()

    # get the routes blueprint
    from .routes import routes
    app.register_blueprint(routes)
    return app