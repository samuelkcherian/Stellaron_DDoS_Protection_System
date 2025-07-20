#backend app.py
from flask import Flask 
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def home():
    logging.info("Request received successfully.")
    return "<h1>Welcome to the Protected Service! ✅</h1>"

if __name__ == '__main':
    app.run(host='0.0.0.0', port=5000)