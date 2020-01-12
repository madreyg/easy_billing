from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
import os


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DBConnect(metaclass=Singleton):
    pg_pool = None

    def connect(self):
        if self.pg_pool is None:
            try:
                pg_pool = psycopg2.pool.ThreadedConnectionPool(os.getenv('SQL_CONNECTION_POOL_MIN'),
                                                               os.getenv('SQL_CONNECTION_POOL_MAX'),
                                                               user=os.getenv('POSTGRES_USER'),
                                                               password=os.getenv('POSTGRES_PASSWORD'),
                                                               host=os.getenv('SQL_HOST'),
                                                               port=os.getenv('SQL_PORT'),
                                                               database=os.getenv('POSTGRES_DB'))
                if pg_pool:
                    print("Connection pool created successfully using ThreadedConnectionPool")
                    self.pg_pool = pg_pool
            except Exception as err:
                print("Connection pool didn't created using ThreadedConnectionPool", err)
        return self.pg_pool


@contextmanager
def get_db_connection():
    db_conn = DBConnect()
    pg_pool = db_conn.connect()
    connection = pg_pool.getconn()
    try:
        yield connection
    finally:
        pg_pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()
