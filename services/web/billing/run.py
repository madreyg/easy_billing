from flask import Flask
from flask_login import LoginManager


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'vG0GnrHWgNXrwSAPcwsG'
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from billing.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(int(user_id))

    # blueprint for auth routes in our app
    from billing.controller.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from billing.controller.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for non-auth parts of app
    from billing.controller.transaction import transaction as transaction_blueprint
    app.register_blueprint(transaction_blueprint)

    # blueprint for non-auth parts of app
    from billing.controller.user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    # 404
    @app.errorhandler(404)
    def not_found(e):
        return "Not founded", 404

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port='8080', debug=True)
