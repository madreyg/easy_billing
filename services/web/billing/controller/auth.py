from http import HTTPStatus

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from billing.models.user import User

auth = Blueprint('auth', __name__)


# for SSR
@auth.route('/login')
def ssr_login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def ssr_login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = find_by_email(email)
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.ssr_login', _external=True)
                        )  # if user doesn't exist or password is wrong, reload the page
    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('user.ssr_user', user_id=user.id, _external=True))


# for api
@auth.route('/api/login/', methods=['POST'])
def api_login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = find_by_email(email)

    if not user or not check_password_hash(user.password, password):
        return "Unautorize", HTTPStatus.UNAUTHORIZED

    login_user(user, remember=remember)
    return "ok", HTTPStatus.OK


def find_by_email(email):
    try:
        return User.find_by_email(email=email)
    except Exception as err:
        return err,


@auth.route('/signup')
def ssr_signup():
    return render_template('signup.html')


@auth.route('/logout')
@login_required
def ssr_logout():
    logout_user()
    return redirect(url_for('main.ssr_index', _external=True))


@auth.route('/signup', methods=['POST'])
def ssr_signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    try:
        user = find_by_email(email)
    except Exception as err:
        return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.ssr_signup'))
    try:
        User(email=email, name=name, password=generate_password_hash(password, method='sha256')).create()
    except Exception as err:
        flash(f'Could not create user. {err}')
        # if a user is found, we want to redirect back to signup page so user can try again
        if user:
            return redirect(url_for('auth.srr_signup'))
    return redirect(url_for('auth.ssr_login'))
