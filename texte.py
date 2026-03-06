from flask import Flask, request
from flask import make_response

app = Flask(__name__)

@app.route("/login")
def login():
    response = make_response("Logado com sucesso")
    response.set_cookie("auth_token", "abc123")
    return response

@app.route('/cookie')
def vercookie():
    token = request.cookies.get("auth_token")
    return token

if __name__ == '__main__':
    app.run()