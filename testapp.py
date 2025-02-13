from flask import Flask
import logging
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initialization log from TEST APPLICATION (develop branch)")  # The initialization log

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/')
def hello():
    return 'Hello World'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))