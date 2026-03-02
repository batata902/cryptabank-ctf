import sqlite3
from flask import Flask, jsonify, request
from core.utils import Utils

# CRUD -> CREATE, READ, UPDATE, DELETE
app = Flask(__name__)

conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript(open('init.sql', 'r').read())

@app.route('/cadastro', methods=["POST"])
def cadastrar():
    infos = request.get_json()
    
    account_id = Utils.uuid()
    data_atual = Utils.get_local_date()

    conn.execute('INSERT INTO users(nome, cpf, email, senha, conta_id, created_at, currency) VALUES(?, ?, ?, ?, ?, ?, ?, ?)', (infos['nome'], infos['cpf'], infos['email'], infos['senha'], account_id, data_atual, 0));
    conn.commit()
    return jsonify({'status': 'ok'})

@app.route('/login', methods=["POST"])
def login():
    None


def delete():
    None


def update():
    None


if __name__ == '__main__':
    app.run(debug=True)