import sqlite3
from cryptabank.core.utils import Utils
import requests

# CRUD -> CREATE, READ, UPDATE, DELETE

class Model:

    def __init__(self):
        self.conn = sqlite3.connect('database.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self.cur.executescript(open('init.sql', 'r').read())


    def is_auth(self, cookie):
        consulta = self.cur.execute('SELECT cookie FROM users_cookies WHERE cookie=?;', (cookie,)).fetchone()
        if consulta:
            return True
        return False
    
    def get_cookie(self, email):
        cookie = self.cur.execute('SELECT cookie FROM users_cookies WHERE email=?', (email,)).fetchone()
        return cookie['cookie']


    def save_cookie(self, cookie, email):
        self.conn.execute('INSERT INTO users_cookies(cookie, email) VALUES (?, ?);', (cookie, email))
        self.conn.commit()

    def delete_cookie(self, token):
        self.conn.execute('DELETE FROM users_cookies WHERE cookie=?', (token,))
        self.conn.commit()

    def email_cookie(self, cookie):
        consulta = self.cur.execute('SELECT email FROM users_cookies WHERE cookie=?', (cookie,)).fetchone()
        return consulta['email']

    def get_user_infos(self, token):
        email = self.email_cookie(token)
        consulta = self.cur.execute('SELECT nome, conta_id, email FROM users WHERE email=?', (email,)).fetchone()
        return dict(consulta)
    
    def get_all_user_infos(self, token):
        email = self.email_cookie(token)
        consulta = self.cur.execute('SELECT * FROM users WHERE email=?;', (email,)).fetchone()
        return dict(consulta)


    def cadastrar(self, infos):
        data_atual = Utils.get_local_date()

        try:
            self.conn.execute('INSERT INTO users(nome, cpf, email, senha, conta_id, created_at) VALUES(?, ?, ?, ?, ?, ?)', (infos['nome'], infos['cpf'], infos['email'], infos['senha'], infos['account_id'], data_atual));
            self.conn.commit()

            requests.post('http://127.0.0.1:9999/api/registrar-user', json=infos) # Registra no db interno dados de conta
        except KeyError:
            return False
        return True


    def login(self, infos):
        consulta = self.cur.execute('SELECT email, senha FROM users WHERE email = ? AND senha = ?', (infos['email'], infos['senha'])).fetchone()

        if consulta:
            return True
        return False

    def registrar_mensagem(self, mensagem, token):
        email = self.email_cookie(token)
        self.conn.execute('INSERT INTO mensagens_suporte(categoria, assunto, problema, email) VALUES(?, ?, ?, ?)', (mensagem['cat'], mensagem['titulo'], mensagem['problema'], email))
        self.conn.commit()

    def show_all_suport_messages(self):
        consulta = self.cur.execute('SELECT * FROM mensagens_suporte;').fetchall()
        
        return [dict(row) for row in consulta]

    def save_transfer(self, transfer):
        if int(transfer['valor']) < 0:
            self.conn.execute('UPDATE users SET currency=? WHERE email=?;', (int(transfer['currency']) + int(transfer['valor']), transfer['email']))
        self.conn.execute('INSERT INTO transfer_history(source_wallet, destiny_wallet, value, transfer_status) VALUES (?, ?, ?, "pending");', (transfer['conta_id'], transfer['destino'], transfer['valor']))
        self.conn.commit()

    def account_exists(self, account_id):
        consulta = self.cur.execute('SELECT * FROM users WHERE conta_id=?', (account_id,)).fetchone()
        if consulta:
            return True
        return False

    # DEV TOOLS

    def set_currency(self, valor, email):
        self.conn.execute('UPDATE users SET currency=? WHERE email=?;', (valor, email))
        self.conn.commit()
