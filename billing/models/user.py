from decimal import Decimal

from models.db import get_db_cursor
from models.invoice import Invoice
from models.currency import EUR, USD, CNY


class User:
    def __init__(self, u_id=0, name=''):
        self.id = u_id
        self.name = name
        self.created_at = None
        self.invoices = {EUR: None, USD: None, CNY: None}

    def __insert(self, cur):
        cur.execute(
            '''
            INSERT INTO public.user (id, name, created_at) VALUES
                                (%s::int, %s::text, now()) RETURNING created_at, id;
            ''', (self.id, self.name))
        created_at, u_id = cur.fetchone()
        return created_at, u_id

    def __create(self, cur):
        created_at, u_id = self.__insert(cur)
        self.id = u_id
        self.created_at = created_at
        invoice_usd = Invoice.new_empty(user_id=u_id, currency=USD, balance=Decimal(100)).create(cur)
        invoice_eur = Invoice.new_empty(user_id=u_id, currency=EUR).create(cur)
        invoice_cny = Invoice.new_empty(user_id=u_id, currency=CNY).create(cur)
        self.invoices = {USD: invoice_usd, EUR: invoice_eur, CNY: invoice_cny}

    def create(self, cur=None):
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                self.__create(cur)
        else:
            self.__create(cur)
        return self
