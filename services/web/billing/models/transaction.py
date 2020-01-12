import uuid
from decimal import Decimal, Context, ROUND_DOWN

from billing.models.db import get_db_cursor
from billing.models.invoice import Invoice

COMMISSION = 0.01

SUCCESS = 0
IN_PROCESS = 1
CANCELED = -1

TWOPLACES = Decimal(10) ** -2


class Transaction:
    """
    create transaction and start it with special business logic
    """

    def __init__(self, inv_id_from, inv_id_to, amount, id=None, uid=None, created_at=None, updated_at=None,
                 status=None):
        self.id = 0 if id is None else id
        self.invoice_id_from = int(inv_id_from)
        self.invoice_id_to = int(inv_id_to)
        if isinstance(amount, Decimal):
            self.amount = amount.quantize(TWOPLACES)
        else:
            self.amount = Decimal(amount).quantize(TWOPLACES)

        self.uid = str(uuid.uuid4()) if uid is None else uid
        self.created_at = created_at
        self.updated_at = updated_at
        self.status = 1 if status is None else status

    def get_status(self):
        return self.status

    def __create(self, cur):
        cur.execute(
            '''                                                           
             WITH new_tr AS (
                INSERT INTO "transaction" ( uuid, invoice_id_from, invoice_id_to, amount, created_at, status)
                SELECT %(uuid)s::UUID, %(inv_id_from)s::INT, %(inv_id_to)s::INT, %(amount)s::NUMERIC(32,2), now(), %(status)s::INT
                WHERE NOT EXISTS (SELECT 1 
                      FROM "transaction"
                      WHERE uuid = %(uuid)s::UUID)
                RETURNING created_at, id
                )
             SELECT * FROM new_tr
             UNION
             SELECT created_at, id FROM "transaction" WHERE  uuid = %(uuid)s::UUID;     
                              
            ''', {"uuid": str(self.uid),
                  "inv_id_from": self.invoice_id_from,
                  "inv_id_to": self.invoice_id_to,
                  "amount": self.amount,
                  "status": IN_PROCESS})
        created_at, id = cur.fetchone()
        return created_at, id

    def create(self, cur=None):
        """
        create transactions in db
        :param cur: psycopg2.cursor
        """
        if not self.invoice_id_from:
            raise Exception("Bad invoice from")
        if not self.invoice_id_to:
            raise Exception("Bad invoice to")
        if self.invoice_id_from == self.invoice_id_to:
            raise Exception("Transaction don't create between one account")
        if cur is None:
            with get_db_cursor(commit=True) as cur:
                created_at, id = self.__create(cur)
        else:
            created_at, id = self.__create(cur)
        self.id = id
        self.created_at = created_at
        return self

    def __eq__(self, other):
        return self.id == other.id and \
               self.uid == other.uid and \
               self.invoice_id_from == other.invoice_id_from and \
               self.invoice_id_to == other.invoice_id_to and \
               self.created_at == other.created_at and \
               self.updated_at == other.updated_at and \
               str(self.amount) == str(other.amount) and \
               self.status == other.status

    def run(self):
        """
        run transaction with special logic
        """
        tr = Transaction.find_by_id(self.id)
        if not tr:
            raise Exception('Transaction had to fix (created in db) ')
        if tr.get_status() != IN_PROCESS:
            raise Exception(f'Transaction completed yet with status {tr.get_status()}')
        if tr != self:
            raise Exception("Transaction object not synchronize with db")
        with get_db_cursor(commit=False) as cur:
            try:
                invoice_from = Invoice.find_by_id(self.invoice_id_from)
                invoice_to = Invoice.find_by_id(tr.invoice_id_to)
                if invoice_from.user_id == invoice_to.user_id:
                    self.__move_internal(invoice_from, invoice_to, cur)
                else:
                    self.__move_external(invoice_from, invoice_to, cur)
                self.__update_status(SUCCESS, cur)
                cur.connection.commit()
                return self
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
        context = Context(prec=1, rounding=ROUND_DOWN)
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
              UPDATE "transaction" SET (status, updated_at) = (%s::INT, now()) WHERE id = %s::INT RETURNING updated_at;
            ''', (status, self.id))
        updated = cur.fetchone()
        if updated:
            self.updated_at = updated[0]
        self.status = status

    def canceled(self, cur=None):
        """
        cancel run transaction, add status CANCELED
        :param cur:
        """
        if cur:
            self.__update_status(CANCELED, cur)
        with get_db_cursor(commit=True) as cur:
            self.__update_status(CANCELED, cur)

    @staticmethod
    def find_by_id(id):
        """
        transaction select by id
        :param id: transaction id
        :return: Transaction object or None
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                '''SELECT uuid, invoice_id_from, invoice_id_to, created_at, updated_at, amount, status 
                   FROM public.transaction WHERE id=%s::INT LIMIT 1''',
                (id,))
            result = cur.fetchone()
            if result:
                uid, inv_id_from, inv_id_to, created_at, updated_at, amount, status = result
                return Transaction(inv_id_from, inv_id_to, amount,
                                   uid=uid, created_at=created_at, updated_at=updated_at, id=id, status=status)
        return None

    @staticmethod
    def __build_from_flt(flt, aliases):

        flt_list = []
        flt_params = []

        def build_fields_flt(val, tname):
            res_lst = []
            for key_inn, val_inn in val.items():
                fname = key_inn
                for item in val_inn:
                    res_lst.append(f"{tname}.{fname} {item['operation']} %s ")
                    flt_params.append(item['value'])
            return res_lst

        for key, val in flt.items():
            if key == "composite":
                for item in val:
                    composite_list = []
                    for key_c, val_c in item.items():
                        tmp_list = build_fields_flt(val_c, aliases[key_c])
                        composite_list.extend(tmp_list)
                    composite_str = " ( " + " OR ".join(composite_list) + " ) "
                    flt_list.append(composite_str)
            else:
                fields_lst = build_fields_flt(val, aliases[key])
                flt_list.extend(fields_lst)
        return "WHERE " + " AND ".join(flt_list), flt_params

    @staticmethod
    def __build_from_srt(srt, aliases):
        srt_list = []
        for table, fields in srt.items():
            tname = aliases[table]
            for field, operation in fields.items():
                srt_list.append(f"{tname}.{field} {operation}")
        return "ORDER BY " + ", ".join(srt_list)

    @staticmethod
    def __build_from_nav(nav):
        limit_str = f"limit {nav['limit']}" if nav.get('limit', None) else ""
        offset_str = f"offset {nav['offset']}" if nav.get('offset', None) else ""
        return limit_str + " " + offset_str

    @staticmethod
    def find(flt=None, srt=None, nav=None):
        """
        transaction select by id
        :param flt: dict  - include filtering rules {"<table>":{"<field>":[{'operation': <name>, 'value':<value>}]}}
               For example: {"composite": {"invoice_from": {"user_id": [{'operation': 'eq', 'value':243}]},
                                           "invoice_to": {"user_id": [{'operation': 'eq', 'value':243}]}}},
                             "transaction": {"created_at": [{'operation': 'lt', 'value':'2020-01-10'},
                                                            {'operation': 'gt', 'value':'2020-01-10'}]}},
                             }
        :param srt: dict - include sorting rules {"<table>": {"<field>":"<value>"}}
                For example: {"transaction": {"created_at": "asc"}}
        :param nav: dict - include navigation rules {"limit": "<value>", "offset": "value"}
                For example: {"limit": 10, "offset":10}
        :return: list Transactions object with shorten information about invoices
        """
        aliases = {
            'transaction': 'tr',
            'invoice_from': 'inv_from',
            'invoice_to': 'inv_to',
            'currency_from': 'cur_from',
            'currency_to': 'cur_to'
        }
        params = []

        flt_str = ""
        if flt:
            flt_str, flt_params = Transaction.__build_from_flt(flt, aliases)
            params.extend(flt_params)
        srt_str = Transaction.__build_from_srt(srt, aliases) if srt else ""
        # todo: доделать навигацию
        nav_str = Transaction.__build_from_nav(nav) if nav else ""
        trans_list = []
        with get_db_cursor(commit=True) as cur:
            sql = f'''SELECT
                      tr.*
                    FROM transaction tr
                      left join invoice inv_from on tr.invoice_id_from = inv_from.id
                      left join currency cur_from on inv_from.currency_id = cur_from.id
                      left join invoice inv_to on tr.invoice_id_to = inv_to.id
                      left join currency cur_to on inv_to.currency_id = cur_to.id
                    {flt_str}
                    {srt_str};
                '''
            cur.execute(sql, params)
            result = cur.fetchall()
            if result:
                for item in result:
                    id, uid, inv_id_from, inv_id_to, created_at, updated_at, amount, status = item
                    trans_list.append(
                        Transaction(inv_id_from, inv_id_to, amount, id=id, uid=uid, created_at=created_at,
                                    updated_at=updated_at, status=status))
                return trans_list
            return []

    def __str__(self):
        return f"id: {self.id}, uid: {self.uid}, invoice_id_from: {self.invoice_id_from}," \
               f"invoice_id_to {self.invoice_id_to},created_at {self.created_at}," \
               f"updated_at {self.updated_at},amount {self.amount},status {self.status}"

    def serialize(self) -> dict:
        """
        ready object for http send
        :return: dict with converted type for http send
        """
        return {
            "id": self.id,
            "invoice_id_from": self.invoice_id_from,
            "invoice_id_to": self.invoice_id_to,
            "amount": str(self.amount),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.get_status(),
            "uuid": self.uid,
        }
