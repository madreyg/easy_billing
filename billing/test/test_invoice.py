import psycopg2
import pytest
from decimal import Decimal

from models.currency import USD, EUR
from models.db import get_db_cursor
from models.invoice import Invoice
from models.user import User


@pytest.fixture(scope="function")
def cur():
    with get_db_cursor(commit=False) as cur:
        yield cur


@pytest.fixture(scope="function")
def user(cur):
    user_name = "new_user_test"
    user_id = 117
    user = User(u_id=user_id, name=user_name).create(cur)
    return user


def test_create(cur, user):
    invoice = Invoice.new_empty(user_id=user.id, currency=USD, balance=Decimal(500)).create(cur=cur)
    cur.execute(
        f'''SELECT id,user_id,currency_id,balance,created_at,updated_at FROM public.invoice where id = {invoice.id}''')
    id, user_id, currency_id, balance, created_at, updated_at = cur.fetchone()
    assert id == invoice.id, "Bad invoice id in saved object"
    assert user_id == invoice.user_id, "Bad invoice user_id in saved object"
    assert balance == invoice.balance, "Bad invoice balance in saved object"
    assert created_at == invoice.created_at, "Bad invoice created_at in saved object"
    assert updated_at == invoice.updated_at, "Bad invoice updated_at in saved object"
    assert currency_id == invoice.currency.id, "Bad invoice currency_id in saved object"


def test_update_balance_add(cur, user):
    invoice = user.invoices.get(USD, None)
    invoice.update_balance_add(-Decimal(50), cur)
    cur.execute(
        f'''SELECT balance,updated_at FROM public.invoice where id = {invoice.id}''')
    balance, updated_at = cur.fetchone()
    assert invoice.balance - Decimal(50) == balance, "Didn't update balance"
    assert updated_at is not None, "Didn't update updated_at"
    assert invoice.created_at <= updated_at, "Didn't update updated_at"

    invoice = user.invoices.get(EUR, None)
    try:
        invoice.update_balance_add(-Decimal(50), cur)
    except psycopg2.IntegrityError as err:
        assert isinstance(err, psycopg2.errors.CheckViolation)


def test_find_by_id(cur, user):
    invoice = user.invoices.get(USD, None)
    invoice_new = Invoice.find_by_id(invoice.id, cur)
    assert invoice == invoice_new
