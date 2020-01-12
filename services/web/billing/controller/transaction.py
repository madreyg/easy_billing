from decimal import Decimal

import datetime
from http import HTTPStatus

from flask import Blueprint, request, url_for, redirect, flash, render_template
from flask_login import login_required, current_user

from billing.controller.validation import valid_user_ssr, valid_user_api
from billing.models.currency import USD, EUR, CNY
from billing.models.transaction import Transaction, SUCCESS

transaction = Blueprint('transaction', __name__)


# for SSR
@transaction.route('/user/<user_id>/transaction/', methods=['POST'])
@login_required
def ssr_transaction_create_handler(user_id):
    try:
        err = valid_user_ssr(user_id)
        if err:
            return err
    except Exception as err:
        return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
    invoice_from = request.form.get('from')
    invoice_to = request.form.get('to')
    amount = Decimal(request.form.get('amount'))
    try:
        msg, is_err = transaction_create(invoice_from, invoice_to, amount)
    except Exception as err:
        is_err = True
        msg = err
    # for type notification
    flash(not is_err)
    flash(f'Result: {msg}')
    return redirect(
        url_for('user.ssr_user', user_id=user_id))  # if user doesn't exist or password is wrong, reload the page


# for api
@transaction.route('/api/user/<user_id>/transaction/', methods=['POST'])
def api_transaction_create(user_id):
    try:
        err = valid_user_api(user_id)
        if err:
            return err
    except Exception as err:
        return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
    invoice_from = request.form.get('from')
    invoice_to = request.form.get('to')
    amount = Decimal(request.form.get('amount'))
    try:
        msg, _ = transaction_create(invoice_from, invoice_to, amount)
    except Exception as err:
        return err, HTTPStatus.INTERNAL_SERVER_ERROR
    return msg, HTTPStatus.CREATED


def transaction_create(invoice_from, invoice_to, amount):
    """
    create and run transaction
    :param amount: Decimal
    :param invoice_to: int
    :param invoice_from: int
    :return:
    """
    try:
        tr = Transaction(invoice_from, invoice_to, amount).create()
    except Exception as err:
        raise Exception("Didn't create transaction. ", err)
    try:
        tr = tr.run()
        msg = 'succsess' if tr.get_status() == SUCCESS else 'fail'
        is_err = False
    except Exception as err:
        print("Transaction running problem", err)
        msg = "Failed. " + str(err)
        is_err = True
    return msg, is_err


@transaction.route('/user/<user_id>/transaction/', methods=['GET'])
@login_required
def ssr_transactions(user_id):
    try:
        err = valid_user_ssr(user_id)
        if err:
            return err
    except Exception as err:
        return err, HTTPStatus.INTERNAL_SERVER_ERROR
    result = transactions_handler_base(user_id)
    return render_template('transactions.html', transactions=result, user_id=user_id,
                           last_day=datetime.date.today() - datetime.timedelta(days=1),
                           invoice_usd=current_user.invoices.get(USD, None),
                           invoice_eur=current_user.invoices.get(EUR, None),
                           invoice_cny=current_user.invoices.get(CNY, None),
                           current_url=request.full_path)


@transaction.route('/api/user/<user_id>/transaction/', methods=['GET'])
def api_transactions(user_id):
    try:
        err = valid_user_api(user_id)
        if err:
            return err
    except Exception as err:
        return err, HTTPStatus.INTERNAL_SERVER_ERROR

    result = transactions_handler_base(user_id)
    return [tr.serialize() for tr in result], HTTPStatus.OK


def transactions_handler_base(user_id):
    flt_str = request.args.get('filter', default='', type=str)
    srt_str = request.args.get('sort', default='', type=str)

    # by default
    flt = {"composite": [{"invoice_from": {"user_id": [{"operation": "=", "value": int(user_id)}]},
                          "invoice_to": {"user_id": [{"operation": "=", "value": int(user_id)}]}}],
           "transaction": {"status": [{"operation": "=", "value": SUCCESS}]}}
    try:
        __parse_flt(flt_str, flt)
        srt = __parse_srt(srt_str, )
        result = Transaction.find(flt, srt)
    except Exception as err:
        return err, HTTPStatus.FORBIDDEN
    return result


def __parse_field(field, operation, cls):
    ids = []
    for el in field.split(','):
        try:
            if cls == int or str:
                ids.append({'operation': operation, 'value': cls(el)})
            if cls == datetime.date:
                ids.append({'operation': operation, 'value': cls.fromisoformat(el)})
        except ValueError as err:
            print("bad value in filter. ignored. ", err)
    return ids


def __parse_flt(flt, flt_obj=None):
    if not flt_obj:
        flt_obj = {}
    parts = flt.split(';')
    # todo: продумать более лаконичную систему работы с фильтрами
    for part in parts:
        field = part.split(' ')
        if len(field) == 3:
            if field[0] == 'invoice':
                ids = __parse_field(field[2], "=", int)
                com_tmp_lst = flt_obj.get("composite", [])
                com_tmp_lst.append({"invoice_from": {"id": ids}, "invoice_to": {"id": ids}})
                flt_obj["composite"] = com_tmp_lst
            elif field[0] == 'user':
                ids = __parse_field(field[2], "=", int)
                flt_obj["invoice_from"] = {"user_id": ids}
                flt_obj["invoice_to"] = {"user_id": ids}
            elif field[0] == 'created_at':
                ids = __parse_field(field[2], ">", datetime.date)
                flt_obj["transaction"] = {"created_at": ids}


def __parse_srt(srt, srt_obj=None):
    if not srt_obj:
        srt_obj = {}
    parts = srt.split(';')
    # todo: продумать более лаконичную систему работы с сортировкой
    for part in parts:
        field = part.split(' ')
        print("field", field)
        if len(field) == 2:
            if field[0] == 'created_at':
                order = "asc" if field[1] == "asc" else "desc"
                srt_obj.setdefault("transaction", {}).setdefault("created_at", order)
                return srt_obj
