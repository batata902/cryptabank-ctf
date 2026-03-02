from flask import Flask

app = Flask(__name__)

from cryptabank.routes import homepage