from models.db import get_db_cursor

USD = 'USD'
EUR = 'EUR'
CNY = 'CNY'


class Currency:
    def __init__(self, name):
        self.name = name
        self.__get_by_name()

    def __get_by_name(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute('''SELECT id, rate_usd FROM currency WHERE name=%s::VARCHAR(8) limit 1;''', (self.name,))
            self.id, self.rate_usd = cur.fetchone()

    def __eq__(self, other):
        return self.id == other.id
