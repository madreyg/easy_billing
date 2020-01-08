from flask import Flask
from flask_login import LoginManager

from db import db

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'vG0GnrHWgNXrwSAPcwsG'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from controller import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for non-auth parts of app
    from invoice import invoice as invoice_blueprint
    app.register_blueprint(invoice_blueprint)

    return app


if __name__ == '__main__':
    db.create_all(app=create_app())
