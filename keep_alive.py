from flask import Flask
from threading import Thread

from config import KEEP_ALIVE_PORT

app = Flask(__name__)


@app.route("/")
def home():
    return "J.A.R.V.I.S is online, Sir."


@app.route("/health")
def health():
    return {"status": "ok"}


def run():
    app.run(host="0.0.0.0", port=KEEP_ALIVE_PORT)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
