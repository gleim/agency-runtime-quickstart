from flask import Flask
from threading import Thread
from waitress import serve

app = Flask('')

@app.route('/')
def home():
    return "Agent liveness confirmed"

def run():
  #app.run(host='0.0.0.0',port=8080)
  serve(app, url_scheme='https')

def keep_alive():
    t = Thread(target=run)
    t.start()