import pytest
from decimal import Decimal

from models.currency import USD, EUR, CNY
from models.db import get_db_cursor
from models.user import User


@pytest.fixture(scope="module")
def user():
    user_name = "new_user_test"
    user_id = 117
    return User(u_id=user_id, name=user_name)


def test_create(user):
    with get_db_cursor(commit=False) as cur:
        user.create(cur)
        cur.execute(f'''SELECT id, name, created_at FROM public.user WHERE id = {user.id} limit 1;''')
        u_id, name, created_at = cur.fetchone()
        assert u_id == user.id, "Bad id in saved user"
        assert name == user.name, "Bad name in saved user"
        assert created_at is not None, "Bad created_at in saved user"
        invoice_usd = user.invoices.get(USD, None)
        assert invoice_usd is not None, "Bad invoice USD in saved user"
        assert invoice_usd.balance == Decimal(100), "Bad invoice USD balance in saved user"

        invoice_eur = user.invoices.get(EUR, None)
        assert invoice_eur is not None, "Bad invoice EUR in saved user"
        assert invoice_eur.balance == Decimal(0), "Bad invoice EUR balance in saved user"

        invoice_cny = user.invoices.get(CNY, None)
        assert invoice_cny is not None, "Bad invoice CNY in saved user"
        assert invoice_cny.balance == Decimal(0), "Bad invoice CNY balance in saved user"
