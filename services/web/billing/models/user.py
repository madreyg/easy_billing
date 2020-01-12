from decimal import Decimal

from flask_login import UserMixin

from billing.models.db import get_db_cursor
from billing.models.invoice import Invoice
from billing.models.currency import EUR, USD, CNY


class User(UserMixin):
    def __init__(self, u_id=0, name='', email='', password='', created_at=None, invoice_ids=()):
        self.id = u_id
        self.name = name
        self.invoices = {EUR: None, USD: None, CNY: None}
        self.email = email
        self.password = password
        self.created_at = created_at
        if invoice_ids:
            for item in invoice_ids:
                inv = Invoice.find_by_id(item)
                self.invoices[inv.currency.name] = inv

    def __insert(self, cur):
        cur.execute(
            '''
            INSERT INTO "user" (name, created_at, email, password) VALUES 
            ( %s::TEXT, now(), %s::TEXT, %s::TEXT ) 
            RETURNING created_at, id;
            ''', (self.name, self.email, self.password))
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
        """
        create user in db
        :param cur: psycopg2.Cursor - need for postgresql transaction
        :return: self
        """
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                self.__create(cur)
        else:
            self.__create(cur)
        return self

    @staticmethod
    def find_by_email(email: str):
        """
        find user by email. email - unique param
        :param email: srt - email user
        :return: User object
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute('''SELECT u.id,
                                  u.created_at,
                                  u.name,
                                  u.password,
                                  array_agg(invoice.id)
                            FROM public."user" u
                            LEFT JOIN invoice ON u.id = invoice.user_id
                            WHERE u.email=%s::TEXT 
                            GROUP BY u.id, u.created_at, u.name, u.password
                            LIMIT 1''', (email,))
            data = cur.fetchone()
            if data:
                u_id, created_at, name, password, invoice_ids = data
                return User(u_id=u_id, name=name, email=email, password=password, created_at=created_at,
                            invoice_ids=invoice_ids)
            return None

    @staticmethod
    def find_by_id(u_id: int):
        """
        find user by id
        :param u_id: int - id user
        :return: User object
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute('''SELECT u.email, 
                                  u.created_at, 
                                  u.name, 
                                  u.password, 
                                  array_agg(invoice.id)
                            FROM "user" u
                              LEFT JOIN invoice ON u.id = invoice.user_id
                            WHERE u.id = %s::INT
                            GROUP BY u.email, u.created_at, u.name, u.password
                            LIMIT 1''', (u_id,))
            data = cur.fetchone()
            if data:
                email, created_at, name, password, invoice_ids = data
                user = User(u_id=u_id, name=name, email=email, password=password, created_at=created_at,
                            invoice_ids=invoice_ids)
                return user
            return None

    def __str__(self):
        return f"User(id:{self.id},email:{self.email},name:{self.name},invoices:{self.invoices})"

    def serialize(self):
        """
         ready object for http send
         :return: dict with converted type for http send
         """
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "invoices": {
                USD: self.invoices.get(USD, None).serialize() if self.invoices.get(USD, None) else None,
                EUR: self.invoices.get(EUR, None).serialize() if self.invoices.get(EUR, None) else None,
                CNY: self.invoices.get(CNY, None).serialize() if self.invoices.get(CNY, None) else None
            },
            "email": self.email
        }
