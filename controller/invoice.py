from flask import Blueprint, render_template
from flask_login import login_required, current_user

invoice = Blueprint('invoice', __name__)


@invoice.route('/invoices')
@login_required
def invoices():
    print(current_user.__dict__)
    return render_template('invoices.html', name=current_user.name)
