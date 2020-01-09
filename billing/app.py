from flask import Flask
#
# from models.db import get_db_cursor
#
# app = Flask(__name__)
#
#
# @app.route('/', methods=['GET'])
# def get_tasks():
#     with get_db_cursor(commit=True) as cur:
#         cur.execute("SELECT ")
#     return "Hello world"
#
#
# if __name__ == '__main__':
#     initdb()
#     app.run(host='0.0.0.0', port='8002', debug=True)




from kafka import KafkaConsumer

if __name__ == '__main__':
    consumer = KafkaConsumer('billing_topic', group_id='billing_group')
    for msg in consumer:
        print(msg)
