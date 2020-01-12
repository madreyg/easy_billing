import pytest
from decimal import Decimal, ROUND_UP, Context, ROUND_DOWN

from billing.models.currency import USD, EUR
from billing.models.db import get_db_cursor
from billing.models.invoice import Invoice
from billing.models.transaction import Transaction, IN_PROCESS, SUCCESS, COMMISSION, TWOPLACES
from billing.models.user import User
from billing.test.test_invoice import cur, user

amount = Decimal(100)


@pytest.fixture(scope="function")
def user2(cur):
    user_name = "new_user_test"
    user = User(name=user_name, email="user3@mail.ru", password="111111").create(cur)
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
    return Transaction(invoice_usd.id, invoice_eur.id, "48.34").create(cur)


@pytest.fixture(scope="function")
def user_fixed():
    user_name = "new_user_fixed_test"
    user = User(name=user_name, email="user_fixed1@mail.ru", password="111111").create()
    try:
        yield user
    finally:
        with get_db_cursor(commit=True) as cur:
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user.id}::int;''')


@pytest.fixture(scope="function")
def user_fixed2():
    user_name = "new_user_fixed2_test"
    user = User(name=user_name, email="user_fixed2@mail.ru", password="111111").create()
    try:
        yield user
    finally:
        with get_db_cursor(commit=True) as cur:
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user.id}::int;''')


@pytest.fixture(scope="function")
def tr_list_completed(user_fixed, user_fixed2):
    tr_lst = []
    invoice_usd = user_fixed.invoices.get(USD, None)
    invoice_eur = user_fixed2.invoices.get(EUR, None)
    tr_lst.append(Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance // 10).create().run())
    tr_lst.append(Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance // 10).create().run())
    tr_bad = Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance).create()
    try:
        tr_bad.run()
    except Exception as err:
        tr_lst.append(tr_bad)
        print("Badly transaction created: ", err)
    try:
        yield tr_lst
    finally:
        with get_db_cursor(commit=True) as cur:
            for tr in tr_lst:
                cur.execute(f'''DELETE FROM public.transaction WHERE id={tr.id}::int;''')


def test_create_select(cur, user, tr_inner):
    invoice_usd = user.invoices.get(USD, None)
    invoice_eur = user.invoices.get(EUR, None)
    tr_inner2 = Transaction(invoice_usd.id, invoice_eur.id, invoice_usd.balance,
                            id=tr_inner.id,
                            uid=tr_inner.uid,
                            created_at=tr_inner.created_at,
                            updated_at=tr_inner.updated_at,
                            status=tr_inner.get_status()).create(cur)

    assert tr_inner.id == tr_inner2.id, "Bad id in transaction create"
    assert tr_inner.uid == tr_inner2.uid, "Bad uid in transaction create"
    assert tr_inner.invoice_id_from == tr_inner2.invoice_id_from, "Bad invoice_id_from in transaction create"
    assert tr_inner.invoice_id_to == tr_inner2.invoice_id_to, "Bad invoice_id_to in transaction create"
    assert tr_inner.created_at == tr_inner2.created_at, "Bad created_at in transaction create"
    assert tr_inner.updated_at == tr_inner2.updated_at, "Bad updated_at in transaction create"
    assert tr_inner.get_status() == tr_inner2.get_status() == IN_PROCESS, "Bad status in transaction create"
    cur.execute(f'''
            SELECT count(id) 
            FROM public.transaction
            WHERE uuid = '{tr_inner.uid}'::UUID OR uuid = '{tr_inner2.uid}'::UUID''')
    result = cur.fetchone()
    if result:
        count = result[0]
        assert count == 1, 'must be 1 transaction in bd'
    else:
        raise Exception('must be 1 transaction in bd')


def test_create_insert(cur, tr_inner):
    cur.execute(f'''
        SELECT id, uuid, invoice_id_from, invoice_id_to, created_at, updated_at, amount, status 
        FROM public.transaction
        WHERE id = {tr_inner.id}''')
    id, uid, invoice_id_from, invoice_id_to, created_at, updated_at, amount, status = cur.fetchone()
    assert tr_inner.id == id, "Bad id in transaction create"
    assert tr_inner.uid == uid, "Bad uid in transaction create"
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
        context = Context(prec=1, rounding=ROUND_DOWN)
        com = context.create_decimal_from_float(COMMISSION)

        assert inv_from_new.balance == (
            user_invoice_usd.balance - (tr_external.amount + tr_external.amount * com)).quantize(TWOPLACES)
        user_invoice_eur = user2.invoices.get(EUR, None)
        assert inv_to_new.balance == (user_invoice_eur.balance + tr_external.convert_amount(user_invoice_usd,
                                                                                            user_invoice_eur)).quantize(
            TWOPLACES)
    finally:
        with get_db_cursor(commit=True) as cur:
            cur.execute(f'''DELETE FROM public.transaction WHERE id={tr_external.id}::int;''')
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.invoice WHERE user_id={user2.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user.id}::int;''')
            cur.execute(f'''DELETE FROM public.user WHERE id={user2.id}::int;''')


def test_find(tr_list_completed):
    """
    testing without filter
    """
    tr_list_new = Transaction.find()
    invoices = {x.invoice_id_from for x in tr_list_completed} | {x.invoice_id_to for x in tr_list_completed}
    trs = list(filter(lambda x: x.invoice_id_from in invoices or x.invoice_id_to in invoices, tr_list_new))
    sorted(trs, key=lambda x: x.id)
    sorted(tr_list_completed, key=lambda x: x.id)
    for i, v in enumerate(trs):
        print(v)
        print(tr_list_completed[i])
        assert v == tr_list_completed[i]


def test_find_flt_with_status(tr_list_completed, user_fixed):
    """
    testing with filter
    """
    flt_by_default = {"composite": [{"invoice_from": {"user_id": [{"operation": "=", "value": user_fixed.id}]},
                                     "invoice_to": {"user_id": [{"operation": "=", "value": user_fixed.id}]}}],
                      "transaction": {"status": [{"operation": "=", "value": SUCCESS}]}}
    tr_list_new = Transaction.find(flt_by_default)
    assert len(tr_list_new) == len(tr_list_completed) - 1
    sorted(tr_list_new, key=lambda x: x.id)
    sorted(tr_list_completed, key=lambda x: x.id)
    trs = list(filter(lambda x: x.get_status() == SUCCESS, tr_list_completed))
    for i, v in enumerate(trs):
        print(v)
        print(tr_list_new[i])
        assert v == tr_list_new[i]


def test_find_flt_without_status(tr_list_completed, user_fixed):
    """
    testing with filter
    """
    flt_by_default = {"composite": [{"invoice_from": {"user_id": [{"operation": "=", "value": user_fixed.id}]},
                                     "invoice_to": {"user_id": [{"operation": "=", "value": user_fixed.id}]}}]
                      }
    tr_list_new = Transaction.find(flt_by_default)
    assert len(tr_list_new) == len(tr_list_completed)
    sorted(tr_list_new, key=lambda x: x.id)
    sorted(tr_list_completed, key=lambda x: x.id)
    for i, v in enumerate(tr_list_completed):
        print(v)
        print(tr_list_new[i])
        assert v == tr_list_new[i]
