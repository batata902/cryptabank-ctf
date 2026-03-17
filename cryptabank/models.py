import sqlite3
from cryptabank.core.utils import Utils
import requests

# CRUD -> CREATE, READ, UPDATE, DELETE

class Model:

    def __init__(self):
        self.conn = sqlite3.connect('database.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self.cur.executescript(open('schema.sql', 'r').read())


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
    
    def get_user_name_by_transfKey(self, key):
        consulta = self.cur.execute('SELECT nome FROM users WHERE conta_id=?', (key,)).fetchone()
        return dict(consulta)
    
    def get_all_user_infos(self, token):
        email = self.email_cookie(token)
        consulta = self.cur.execute('SELECT * FROM users WHERE email=?;', (email,)).fetchone()
        return dict(consulta)


    def cadastrar(self, infos):
        data_atual = Utils.get_local_date()
        account_id = Utils.uuid()
        infos['conta_id'] = account_id
        infos['created_at'] = data_atual

        try:
            self.conn.execute('INSERT INTO users(nome, cpf, email, senha, conta_id, created_at) VALUES(?, ?, ?, ?, ?, ?);', (infos['nome'], infos['cpf'], infos['email'], infos['senha'], infos['conta_id'], data_atual))
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
        self.conn.execute('INSERT INTO transfer_history(source_wallet, destiny_wallet, valor, transfer_status, descr) VALUES (?, ?, ?, "pending");', (transfer['conta_id'], transfer['destino'], transfer['valor'], transfer['desc']))
        self.conn.commit()

    def get_transactions_history(self, conta_id):
        consulta = self.cur.execute('SELECT * FROM transfer_history WHERE source_wallet=? OR destiny_wallet=?;', (conta_id, conta_id)).fetchall()
        transferencias = [dict(row) for row in consulta]
        for t in transferencias:
            if t['source_wallet'] == conta_id:
                t['valor'] = int(t['valor']) * (-1)

        return transferencias
    
    def get_transaction_by_id(self, id):
        consulta = self.cur.execute('SELECT * FROM transfer_history WHERE id=?', (id,)).fetchone()
        obj = dict(consulta)
        obj['valor'] = int(obj['valor'])

        return obj
    
    def delete_transfer(self, transfer_id):
        self.conn.execute('DELETE FROM transfer_history WHERE id=?', (transfer_id,))
        self.conn.commit()


    # ADMIN PANEL
    def num_chamados(self):
        consulta = dict(self.cur.execute('SELECT COUNT(*) FROM mensagens_suporte;').fetchone())
        
        return consulta['COUNT(*)']
    

    def get_chamado_by_id(self, id):
        consulta = self.cur.execute('SELECT * FROM mensagens_suporte WHERE id=?;', (id,)).fetchone()

        return dict(consulta)
    
    def get_all_chamados(self):
        consulta = self.cur.execute('SELECT * FROM mensagens_suporte;').fetchall()

        return [dict(row) for row in consulta]

    def get_all_users(self):
        consulta = self.cur.execute('SELECT * FROM users;').fetchall()
        users = [dict(row) for row in consulta]

        return users
    
    def get_all_transfs(self):
        consulta = self.cur.execute('SELECT * FROM transfer_history;').fetchall()

        return [dict(row) for row in consulta]

    def count_users(self):
        consulta = dict(self.cur.execute('SELECT COUNT(*) FROM users;').fetchone())
        consulta['num_users'] = consulta['COUNT(*)']
        consulta.pop('COUNT(*)')
        return consulta

    def total_em_contas(self):
        total = requests.get('http://localhost:9999/api/total-em-contas').json()
        return total

    def get_dashboard_infos(self):
        num_users = self.count_users()
        total_contas = self.total_em_contas()

        return num_users | total_contas
