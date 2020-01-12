from http import HTTPStatus

from flask_login import current_user
from werkzeug.utils import redirect


def valid_user_api(user_id):
    """
    validate for ssr (server side rendering)
    :param user_id: str - param from url
    """
    try:
        if int(user_id) != current_user.id:
            return "Forbidden", HTTPStatus.FORBIDDEN
    except ValueError:
        return redirect('/api/404/')


def valid_user_ssr(user_id):
    try:
        if int(user_id) != current_user.id:
            return "Forbidden", HTTPStatus.FORBIDDEN
    except ValueError:
        return redirect('/api/404/')
