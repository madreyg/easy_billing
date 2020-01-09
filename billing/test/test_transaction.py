import pytest
from decimal import Decimal, ROUND_UP, Context

from models.currency import USD, EUR
from models.db import get_db_cursor
from models.invoice import Invoice
from models.transaction import Transaction, IN_PROCESS, SUCCESS, COMMISSION
from models.user import User
from test.test_invoice import cur, user

amount = Decimal(100)


@pytest.fixture(scope="function")
def user2(cur):
    user_name = "new_user_test"
    user_id = 118
    user = User(u_id=user_id, name=user_name).create(cur)
    return user


@pytest.fixture(scope="function")
def tr_inner(cur, user):
    invoice_usd = user.invoices.get(USD, None)
    invoice_eur = user.invoices.get(EUR, None)
    return Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance).create(cur)


@pytest.fixture(scope="function")
def tr_external(cur, user, user2):
    invoice_usd = user.invoices.get(USD, None)
    invoice_eur = user2.invoices.get(EUR, None)
    return Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance // 2).create(cur)


def test_create(cur, tr_inner):
    cur.execute(f'''
        SELECT id, invoice_id_from, invoice_id_to, created_at, updated_at, amount, status 
        FROM public.transaction
        WHERE id = {tr_inner.id}''')
    id, invoice_id_from, invoice_id_to, created_at, updated_at, amount, status = cur.fetchone()
    assert tr_inner.id == id, "Bad id in transaction create"
    assert tr_inner.invoice_id_from == invoice_id_from, "Bad invoice_id_from in transaction create"
    assert tr_inner.invoice_id_to == invoice_id_to, "Bad invoice_id_to in transaction create"
    assert tr_inner.created_at == created_at, "Bad created_at in transaction create"
    assert tr_inner.updated_at == updated_at, "Bad updated_at in transaction create"
    assert tr_inner.get_status() == status == IN_PROCESS, "Bad status in transaction create"


def test_convert_amount(user, tr_inner):
    invoice_usd = user.invoices.get(USD, None)
    invoice_eur = user.invoices.get(EUR, None)
    conv_amount = tr_inner.convert_amount(invoice_usd, invoice_eur)
    rate_eur = invoice_eur.currency.rate_usd
    assert amount / 1 * rate_eur == conv_amount


def test_run_inner(cur, user, tr_inner):
    try:
        # fixed all data
        cur.connection.commit()
        tr_inner.run()
        assert tr_inner.get_status() == SUCCESS
        inv_from_new = Invoice.find_by_id(tr_inner.invoice_id_from)
        inv_to_new = Invoice.find_by_id(tr_inner.invoice_id_to)
        user_invoice_usd = user.invoices.get(USD, None)
        assert inv_from_new.balance == user_invoice_usd.balance - tr_inner.amount
        user_invoice_eur = user.invoices.get(EUR, None)
        assert inv_to_new.balance == user_invoice_eur.balance + tr_inner.convert_amount(user_invoice_usd,
                                                                                        user_invoice_eur)
    finally:
        with get_db_cursor(commit=True) as cur:
            cur.execute(f'''DELETE FROM public.transaction WHERE id={tr_inner.id}::int;''')
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user.id}::int;''')


def test_run_external(cur, user, user2, tr_external):
    try:
        # fixed all data
        cur.connection.commit()
        tr_external.run()
        assert tr_external.get_status() == SUCCESS
        inv_from_new = Invoice.find_by_id(tr_external.invoice_id_from)
        inv_to_new = Invoice.find_by_id(tr_external.invoice_id_to)
        user_invoice_usd = user.invoices.get(USD, None)
        context = Context(prec=1, rounding=ROUND_UP)
        com = context.create_decimal_from_float(COMMISSION)
        assert inv_from_new.balance == user_invoice_usd.balance - (tr_external.amount + tr_external.amount * com)
        user_invoice_eur = user2.invoices.get(EUR, None)
        assert inv_to_new.balance == user_invoice_eur.balance + tr_external.convert_amount(user_invoice_usd,
                                                                                           user_invoice_eur)
    finally:
        with get_db_cursor(commit=True) as cur:
            cur.execute(f'''DELETE FROM public.transaction WHERE id={tr_external.id}::int;''')
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user2.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user2.id}::int;''')
