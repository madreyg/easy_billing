import pytest

from billing.models.db import get_db_cursor
from billing.models.currency import USD, EUR, CNY, Currency


@pytest.fixture(scope="module")
def currency_usd():
    return Currency(name=USD)


@pytest.fixture(scope="module")
def currency_eur():
    return Currency(name=EUR)


@pytest.fixture(scope="module")
def currency_cny():
    return Currency(name=CNY)


def test_currency_usd(currency_usd):
    with get_db_cursor(commit=False) as cur:
        cur.execute(f'''SELECT id, name, rate_usd FROM public.currency WHERE name = '{USD}' limit 1;''')
        id, name, rate_usd = cur.fetchone()
        assert currency_usd is not None
        assert currency_usd.id == id
        assert currency_usd.name == name
        assert currency_usd.rate_usd == rate_usd


def test_currency_eur(currency_eur):
    with get_db_cursor(commit=False) as cur:
        cur.execute(f'''SELECT id, name, rate_usd FROM public.currency WHERE name = '{EUR}' limit 1;''')
        id, name, rate_usd = cur.fetchone()
        assert currency_eur is not None
        assert currency_eur.id == id
        assert currency_eur.name == name
        assert currency_eur.rate_usd == rate_usd


def test_currency_cny(currency_cny):
    with get_db_cursor(commit=False) as cur:
        cur.execute(f'''SELECT id, name, rate_usd FROM public.currency WHERE name = '{CNY}' limit 1;''')
        id, name, rate_usd = cur.fetchone()
        assert currency_cny is not None
        assert currency_cny.id == id
        assert currency_cny.name == name
        assert currency_cny.rate_usd == rate_usd
