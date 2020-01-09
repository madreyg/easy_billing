from decimal import Decimal, Context, ROUND_UP

from models.db import get_db_cursor
from models.invoice import Invoice

COMMISSION = 0.01

SUCCESS = 0
IN_PROCESS = 1
CANCELED = -1


class Transaction:
    """
    create transaction and start it with special business logic
    """

    def __init__(self, inv_id_from=0, inv_id_to=0, amount=Decimal(0)):
        self.id = 0
        self.invoice_id_from = inv_id_from
        self.invoice_id_to = inv_id_to
        self.amount = amount
        self.created_at = None
        self.updated_at = None
        self.__status = 1

    def get_status(self):
        return self.__status

    def __create(self, cur):
        if not self.invoice_id_from:
            raise Exception("Bad invoice from")
        if not self.invoice_id_to:
            raise Exception("Bad invoice to")
        cur.execute(
            '''
            INSERT INTO transaction (invoice_id_from, invoice_id_to, amount, created_at, status) VALUES 
                                    (%s::int, %s::int, %s::numeric(32,0), now(), %s::int ) RETURNING created_at, id;
            ''', (self.invoice_id_from, self.invoice_id_to, self.amount, IN_PROCESS))
        created_at, id = cur.fetchone()
        return created_at, id

    def create(self, cur=None):
        """
        create transactions in db
        :param cur: psycopg2.cursor
        """
        if cur is None:
            cur = get_db_cursor(commit=True)
        created_at, id = self.__create(cur)
        self.id = id
        self.created_at = created_at
        return self

    def run(self):
        """
        run transaction with special logic
        """
        if self.invoice_id_from == 0:
            raise Exception('Account from not provided')
        if self.invoice_id_to == 0:
            raise Exception('Account to not provided')
        if self.amount == Decimal(0):
            raise Exception('Amount not must be 0')
        if not self.is_fixed():
            raise Exception('Transaction had to fix (created in db) ')
        with get_db_cursor(commit=False) as cur:
            try:
                invoice_from = Invoice.find_by_id(self.invoice_id_from)
                invoice_to = Invoice.find_by_id(self.invoice_id_to)
                if invoice_from.user_id == invoice_to.user_id:
                    self.__move_internal(invoice_from, invoice_to, cur)
                else:
                    self.__move_external(invoice_from, invoice_to, cur)
                self.__update_status(SUCCESS, cur)
                cur.connection.commit()
            except Exception as err:
                cur.connection.rollback()
                self.canceled()
                raise err

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
        context = Context(prec=1, rounding=ROUND_UP)
        com = context.create_decimal_from_float(COMMISSION)
        amount_with_commission = self.amount + self.amount * com
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
        """
        converting amount from different currencies of invoices
        :param invoice_from: Invoice move from
        :param invoice_to: Invoice move to
        :return: amount in currency of invoice_to
        """
        if invoice_from.currency.rate_usd != 0:
            return self.amount / invoice_from.currency.rate_usd * invoice_to.currency.rate_usd
        else:
            raise Exception("Bad currency!! rate_usd is 0")

    def __update_status(self, status, cur):
        cur.execute(
            '''
              UPDATE public.transaction SET (status, updated_at) = (%s::int, now()) WHERE id = %s::int;
            ''', (status, self.id))
        self.__status = status

    def canceled(self, cur=None):
        if cur:
            self.__update_status(CANCELED, cur)
        with get_db_cursor(commit=True) as cur:
            self.__update_status(CANCELED, cur)

    def is_fixed(self):
        """
        transaction created in db or not
        :return: bool
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute('''SELECT EXISTS(SELECT id FROM public.transaction WHERE id=%s::int)''', (self.id,))
            result = cur.fetchone()
        return result[0]
