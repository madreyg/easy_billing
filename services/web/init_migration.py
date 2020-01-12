import psycopg2
import os

if __name__ == '__main__':
    conn = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                            password=os.getenv('POSTGRES_PASSWORD'),
                            host=os.getenv('SQL_HOST'),
                            port=os.getenv('SQL_PORT'),
                            database=os.getenv('POSTGRES_DB'))
    cursor = conn.cursor()
    try:
        cursor.execute(open("migrations/initdb.sql", "r").read())
        conn.commit()
    except Exception as err:
        print(err)
    finally:
        cursor.close()
        conn.close()
    print("Tables created.....")
