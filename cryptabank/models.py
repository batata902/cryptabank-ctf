import sqlite3
from contextlib import contextmanager
from cryptabank.core.utils import Utils
import requests

# CRUD -> CREATE, READ, UPDATE, DELETE

DB_PATH = 'database.db'
SCHEMA_PATH = 'schema.sql'

@contextmanager
def get_db():
    """Abre uma conexao nova a cada chamada e fecha ao finalizar."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Inicializa o schema do banco apenas uma vez na startup."""
    with get_db() as conn:
        conn.executescript(open(SCHEMA_PATH, 'r').read())


class Model:

    # --- AUTENTICACAO ---

    def is_auth(self, cookie):
        """Retorna True se o cookie pertence a um usuario comum nao bloqueado."""
        if not cookie:
            return False
        with get_db() as conn:
            row = conn.execute(
                'SELECT uc.email FROM users_cookies uc '
                'JOIN users u ON u.email = uc.email '
                'WHERE uc.cookie=? AND u.bloqueado=0;', (cookie,)
            ).fetchone()
            return bool(row)

    def is_admin(self, cookie):
        """
        Retorna o nivel do admin (0=suporte, 1=admin) ou None se invalido.
        Manter compatibilidade: qualquer valor truthy = tem acesso basico.
        """
        if not cookie:
            return None
        with get_db() as conn:
            row = conn.execute(
                'SELECT a.nivel FROM admin_cookies ac '
                'JOIN admins a ON a.email = ac.email '
                'WHERE ac.cookie=?', (cookie,)
            ).fetchone()
            return row['nivel'] if row else None

    def get_admin_nivel(self, cookie):
        """Retorna 0 (suporte) ou 1 (admin) ou None."""
        return self.is_admin(cookie)

    def get_cookie(self, email):
        with get_db() as conn:
            row = conn.execute(
                'SELECT cookie FROM users_cookies WHERE email=?', (email,)
            ).fetchone()
            return row['cookie'] if row else None

    def get_admin_cookie(self, email):
        with get_db() as conn:
            row = conn.execute(
                'SELECT cookie FROM admin_cookies WHERE email=?', (email,)
            ).fetchone()
            return row['cookie'] if row else None

    def save_cookie(self, cookie, email):
        with get_db() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO users_cookies(cookie, email) VALUES (?, ?);',
                (cookie, email)
            )
            conn.commit()

    def save_admin_cookie(self, cookie, email):
        with get_db() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO admin_cookies(email, cookie) VALUES (?, ?)',
                (email, cookie)
            )
            conn.commit()

    def delete_cookie(self, token):
        with get_db() as conn:
            conn.execute('DELETE FROM users_cookies WHERE cookie=?', (token,))
            conn.commit()

    def email_cookie(self, cookie):
        with get_db() as conn:
            row = conn.execute(
                'SELECT email FROM users_cookies WHERE cookie=?', (cookie,)
            ).fetchone()
            return row['email'] if row else None

    # --- USUARIOS ---

    def get_user_infos(self, token):
        email = self.email_cookie(token)
        if not email:
            return None
        with get_db() as conn:
            row = conn.execute(
                'SELECT nome, conta_id, email FROM users WHERE email=?', (email,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_user_infos(self, token):
        email = self.email_cookie(token)
        if not email:
            return None
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM users WHERE email=?;', (email,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_info_by_id(self, id: int) -> dict:
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_name_by_transfKey(self, key):
        with get_db() as conn:
            row = conn.execute(
                'SELECT nome FROM users WHERE conta_id=?', (key,)
            ).fetchone()
            return dict(row) if row else {'nome': 'Desconhecido'}

    def get_all_users(self):
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM users;').fetchall()
            return [dict(r) for r in rows]

    def cadastrar(self, infos):
        data_atual = Utils.get_local_date()
        account_id = Utils.uuid()
        infos['conta_id'] = account_id
        infos['created_at'] = data_atual

        try:
            with get_db() as conn:
                conn.execute(
                    'INSERT INTO users(nome, cpf, email, senha, conta_id, created_at) '
                    'VALUES(?, ?, ?, ?, ?, ?);',
                    (infos['nome'], infos['cpf'], infos['email'],
                     infos['senha'], infos['conta_id'], data_atual)
                )
                conn.commit()
            requests.post('http://127.0.0.1:9999/api/registrar-user', json=infos, timeout=3)
        except KeyError:
            return False
        return True

    def cadastrar_admin(self, infos):
        """
        infos deve conter: email, senha, nome, nivel (int: 0=suporte, 1=admin)
        """
        try:
            nivel = int(infos.get('nivel', 0))
            nome = infos.get('nome', '')
            with get_db() as conn:
                conn.execute(
                    'INSERT INTO admins(nivel, email, senha, nome) VALUES (?, ?, ?, ?);',
                    (nivel, infos['email'], infos['senha'], nome)
                )
                conn.commit()
        except KeyError:
            return False
        return True

    def get_all_admins(self):
        with get_db() as conn:
            rows = conn.execute('SELECT id, nivel, email, nome FROM admins;').fetchall()
            return [dict(r) for r in rows]

    def admin_login(self, info):
        with get_db() as conn:
            row = conn.execute(
                'SELECT email, senha, nivel FROM admins WHERE email = ? AND senha = ?',
                (info['email'], info['senha'])
            ).fetchone()
            return bool(row)

    def login(self, infos):
        with get_db() as conn:
            # Verifica credenciais E que conta nao esta bloqueada
            row = conn.execute(
                'SELECT email FROM users WHERE email = ? AND senha = ? AND bloqueado = 0',
                (infos['email'], infos['senha'])
            ).fetchone()
            return bool(row)

    def is_bloqueado(self, email):
        with get_db() as conn:
            row = conn.execute(
                'SELECT bloqueado FROM users WHERE email=?', (email,)
            ).fetchone()
            return bool(row['bloqueado']) if row else False

    def bloquear_conta(self, user_id):
        with get_db() as conn:
            conn.execute('UPDATE users SET bloqueado=1 WHERE id=?', (user_id,))
            conn.commit()

    def desbloquear_conta(self, user_id):
        with get_db() as conn:
            conn.execute('UPDATE users SET bloqueado=0 WHERE id=?', (user_id,))
            conn.commit()

    # --- SUPORTE ---

    def registrar_mensagem(self, mensagem, token):
        email = self.email_cookie(token)
        with get_db() as conn:
            conn.execute(
                'INSERT INTO mensagens_suporte(categoria, assunto, problema, email) '
                'VALUES(?, ?, ?, ?)',
                (mensagem['cat'], mensagem['titulo'], mensagem['problema'], email)
            )
            conn.commit()

    def show_all_suport_messages(self):
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM mensagens_suporte;').fetchall()
            return [dict(r) for r in rows]

    def get_all_chamados(self):
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM mensagens_suporte ORDER BY enviado_em DESC;').fetchall()
            return [dict(r) for r in rows]

    def get_chamados_by_token(self, token):
        """Retorna todos os chamados do usuario autenticado pelo token."""
        email = self.email_cookie(token)
        if not email:
            return []
        with get_db() as conn:
            rows = conn.execute(
                'SELECT * FROM mensagens_suporte WHERE email=? ORDER BY enviado_em DESC;', (email,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_chamado_by_id(self, id):
        with get_db() as conn:
            row = conn.execute(
                f'SELECT * FROM mensagens_suporte WHERE id={id};'
            ).fetchone()
            return dict(row) if row else None

    def atualizar_chamado(self, id, status, resposta):
        with get_db() as conn:
            conn.execute(
                'UPDATE mensagens_suporte SET status=?, resposta=? WHERE id=?',
                (status, resposta, id)
            )
            conn.commit()

    def num_chamados(self):
        with get_db() as conn:
            row = conn.execute('SELECT COUNT(*) FROM mensagens_suporte;').fetchone()
            return row[0]

    # --- TRANSFERENCIAS ---

    def save_transfer(self, transfer):
        with get_db() as conn:
            conn.execute(
                'INSERT INTO transfer_history'
                '(source_wallet, destiny_wallet, valor, transfer_status, descr) '
                'VALUES (?, ?, ?, "pending", ?);',
                (transfer['conta_id'], transfer['destino'],
                 transfer['valor'], transfer['desc'])
            )
            conn.commit()

    def get_transactions_history(self, conta_id):
        with get_db() as conn:
            rows = conn.execute(
                'SELECT * FROM transfer_history '
                'WHERE (source_wallet=? OR destiny_wallet=?) '
                "AND destiny_wallet != '' "
                'ORDER BY dia DESC;',
                (conta_id, conta_id)
            ).fetchall()
            result = []
            for row in rows:
                t = dict(row)
                t['valor'] = int(t['valor']) * (-1 if t['source_wallet'] == conta_id else 1)
                result.append(t)
            return result

    def get_transaction_by_id(self, id):
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM transfer_history WHERE id=?', (id,)
            ).fetchone()
            if not row:
                return None
            obj = dict(row)
            obj['valor'] = int(obj['valor'])
            return obj

    def delete_transfer(self, transfer_id):
        with get_db() as conn:
            conn.execute('DELETE FROM transfer_history WHERE id=?', (transfer_id,))
            conn.commit()

    def get_all_transfs(self):
        with get_db() as conn:
            rows = conn.execute(
                'SELECT * FROM transfer_history ORDER BY dia DESC;'
            ).fetchall()
            return [dict(r) for r in rows]

    def get_transf_by_id(self, id):
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM transfer_history WHERE id=?', (id,)
            ).fetchone()
            return dict(row) if row else None

    # --- ADMIN DASHBOARD ---

    def count_users(self):
        with get_db() as conn:
            row = conn.execute('SELECT COUNT(*) FROM users;').fetchone()
            return {'num_users': row[0]}

    def total_em_contas(self):
        try:
            total = requests.get('http://localhost:9999/api/total-em-contas', timeout=3).json()
            return total
        except Exception:
            return {'total': 0}

    def get_dashboard_infos(self):
        num_users = self.count_users()
        total_contas = self.total_em_contas()
        return num_users | total_contas
