from billing.models.db import get_db_cursor
from decimal import Decimal
from billing.models.currency import Currency


class Invoice:
    def __init__(self, id, user_id, currency, balance, created_at, updated_at):
        self.id = id
        self.user_id = user_id
        self.currency = Currency(currency)
        self.balance = balance
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def new_empty(user_id=0, currency='', balance=Decimal(0)):
        id = 0
        user_id = user_id
        balance = balance
        created_at = None
        updated_at = None
        return Invoice(id=id, user_id=user_id, currency=currency, balance=balance, created_at=created_at,
                       updated_at=updated_at)

    def __create(self, cur):
        cur.execute(
            '''
            INSERT INTO invoice (user_id, currency_id, balance, created_at, updated_at) VALUES 
                                (%s::int, %s::int, %s::numeric(32,0), now(),  null ) RETURNING created_at, id;
            ''', (self.user_id, self.currency.id, self.balance))
        created_at, id = cur.fetchone()
        return created_at, id

    def create(self, cur=None):
        """
        create invoice in db
        :param cur: psycopg2.cursor
        :return: self
        """
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                created_at, id = self.__create(cur)
        else:
            created_at, id = self.__create(cur)
        self.id = id
        self.created_at = created_at
        return self

    def __update_balance_add(self, cur, amount):
        cur.execute(
            '''
            UPDATE invoice SET (balance, updated_at) =  
                                (balance + %s::numeric(32,2), now()) where id = %s::int;
            ''', (amount, self.id))

    def update_balance_add(self, amount, cur=None):
        """
        update balace in db in invoice
        :param amount: Decimal
        :param cur: psycopg2.Cursor
        """
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                self.__update_balance_add(cur, amount)
        else:
            self.__update_balance_add(cur, amount)

    @staticmethod
    def __find_by_id(cur, id):
        cur.execute(
            '''
            SELECT invoice.id, invoice.user_id, currency.name, invoice.balance, invoice.created_at, invoice.updated_at 
            FROM public.invoice 
            LEFT JOIN public.currency on currency.id = invoice.currency_id
            WHERE invoice.id=%s::int;
            ''', (id,))
        try:
            id, user_id, currency, balance, created_at, updated_at = cur.fetchone()
            return Invoice(id=id, user_id=user_id, currency=currency, balance=Decimal(balance), created_at=created_at,
                           updated_at=updated_at)
        except ValueError:
            return None

    @staticmethod
    def find_by_id(id, cur=None):
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                return Invoice.__find_by_id(cur, id)
        else:
            return Invoice.__find_by_id(cur, id)

    def __eq__(self, other):
        return self.id == other.id and \
               self.user_id == other.user_id and \
               self.currency == other.currency and \
               self.balance == other.balance and \
               self.created_at == other.created_at and \
               self.updated_at == other.updated_at

    def serialize(self):
        cur = self.currency.serialize()
        return {
            "id": self.id,
            "user_id": self.user_id,
            "currency": cur,
            "balance": str(self.balance),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
