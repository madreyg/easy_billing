from http import HTTPStatus

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from billing.controller.validation import valid_user_ssr, valid_user_api

user = Blueprint('user', __name__)


@user.route('/user/<user_id>/')
@login_required
def ssr_user(user_id):
    try:
        err = valid_user_ssr(user_id)
        if err:
            return err
    except Exception as err:
        return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
    return render_template('profile.html', name=current_user.name, user=current_user)


# for api
@user.route('/api/user/<user_id>/')
def api_user(user_id):
    try:
        err = valid_user_api(user_id)
        if err:
            return err
    except Exception as err:
        return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
    return current_user.serialize(), HTTPStatus.OK
