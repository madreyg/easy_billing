from flask import Flask
from models.db import initdb

app = Flask(__name__)


@app.route('/', methods=['GET'])
def get_tasks():
    return "Hello world"


if __name__ == '__main__':
    initdb()
    app.run(host='0.0.0.0', port='8002', debug=True)
