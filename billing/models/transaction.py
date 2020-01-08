from decimal import Decimal

from models.db import get_db_cursor
from models.invoice import Invoice

COMMISSION = 0.01


class Transaction:
    COMPLETE = 0
    CANCELED = 1

    def __init__(self, inv_id_from=0, inv_id_to=0, amount=Decimal(0)):
        self.id = 0
        self.invoice_id_from = inv_id_from
        self.invoice_id_to = inv_id_to
        self.amount = amount
        self.created_at = None
        self.updated_at = None
        self.__status = 1

    def __create(self, cur):
        cur.execute(
            '''
            INSERT INTO transaction (invoice_id_from, invoice_id_to, amount) VALUE 
                                (%s, %s::int, %s::numeric(32,0) ) RETURNING created_at, id;
            ''', (self.invoice_id_from, self.invoice_id_to, self.amount))
        created_at, id = cur.fetchone()
        return created_at, id

    def create(self, cur=None):
        if cur is None:
            cur = get_db_cursor(commit=True)
        created_at, id = self.__create(cur)
        self.id = id
        self.created_at = created_at

    def run(self):
        if self.invoice_id_from == 0:
            raise Exception('Account from not provided')
        if self.invoice_id_to == 0:
            raise Exception('Account to not provided')
        if self.amount == Decimal(0):
            raise Exception('Amount not must be 0')
        cur = get_db_cursor(commit=False)
        try:
            invoice_from = Invoice.find_by_id(self.invoice_id_from)
            invoice_to = Invoice.find_by_id(self.invoice_id_to)
            if invoice_from.user_id == invoice_to.user_id:
                self.__move_internal(invoice_from, invoice_to, cur)
            else:
                self.__move_external(invoice_from, invoice_to, cur)
            self.update_status(Transaction.COMPLETE, cur)
        except Exception as err:
            cur.rollback()
            print("not success", err)
        cur.commit()

    def __move_internal(self, invoice_from, invoice_to, cur):
        amount = self.convert_amount(invoice_from, invoice_to)
        if amount > 0:
            if invoice_from.balance >= self.amount:
                invoice_from.update_balance_add(-self.amount, cur)
            else:
                raise Exception('Insufficient funds')
            invoice_to.update_balance_add(amount, cur)
        else:
            raise Exception('Insufficient funds')

    def __move_external(self, invoice_from, invoice_to, cur):
        amount_with_commission = self.amount + self.amount * COMMISSION
        if invoice_from.balance >= amount_with_commission:
            invoice_from.update_balance_add(-amount_with_commission, cur)
        else:
            raise Exception('Insufficient funds')

        if invoice_from.currency == invoice_to.currency:
            invoice_to.update_balance_add(self.amount, cur)
        else:
            amount = self.convert_amount(invoice_from, invoice_to)
            if amount > 0:
                invoice_to.update_balance_add(amount, cur)
            else:
                raise Exception('Insufficient funds')

    def convert_amount(self, invoice_from, invoice_to):
        if invoice_from.currency.rate_usd != 0:
            return self.amount / invoice_from.currency.rate_usd * invoice_to.currency.rate_usd
        else:
            raise Exception("Bad currency!! rate_usd is 0")

    def __update_status(self, cur, status):
        cur.execute(
            '''
              UPDATE transaction SET (status, updated_at) = 
                                (%s::int, now()) ;
            ''', (status, self.invoice_id_to))

    def update_status(self, status, cur=None):
        if cur is None:
            cur = get_db_cursor(commit=True)
        self.__update_status(cur, status)
