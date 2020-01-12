from http import HTTPStatus

from flask import Blueprint, render_template

main = Blueprint('main', __name__)


# for SSR
@main.route('/')
def ssr_index():
    return render_template('index.html')


@main.route('/api/404/')
def not_found_api():
    return "Not Founded", HTTPStatus.NOT_FOUND
