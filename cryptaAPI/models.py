import sqlite3

class Database:
    liquidity_id = 'contadeliquidacaoxyz'

    def __init__(self):    
        self.conn = sqlite3.connect('money_system.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self.cur.executescript(open('CryptaBank-CTF/cryptaAPI/init_internal.sql', 'r').read())

        self.conn.execute('INSERT INTO cryptabank (account, is_settlement, currency) SELECT ?, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM cryptabank WHERE account = ?);', (self.liquidity_id, self.liquidity_id))
        self.conn.commit()


    def registrar(self, infos):
        print(infos)
        self.conn.execute('INSERT INTO users(email, conta_id, created_at, currency) VALUES (?, ?, ?, ?);', (infos['email'], infos['conta_id'], infos['created_at'], 0))
        self.conn.commit()


    def send_to_liquidity(self, source, value):
        self.cur.execute(
            'UPDATE users SET currency = currency + ? WHERE conta_id=?',
            (int(value), source)
        )

        self.cur.execute(
            'UPDATE cryptabank SET currency = currency + ? WHERE account=?',
            (int(value)*(-1), self.liquidity_id)
        )


    def see_liquidity(self):
        consulta = self.cur.execute('SELECT * FROM cryptabank WHERE account=?', (self.liquidity_id,)).fetchone()
        return dict(consulta)


    def save_transaction(self, transactions_infos):
        self.cur.execute('INSERT INTO transactions(source, source_currency, destiny, quantity, transaction_status) VALUES (?, ?, ?, ?, ?)', (transactions_infos['conta_id'], transactions_infos['currency'], transactions_infos['destino'], transactions_infos['valor'], transactions_infos['transaction_status']))

        transaction_id = self.cur.lastrowid
        print('\033[35mID DA ULTIMA TRANSACAO: \033[m')
        print(transaction_id)
        return transaction_id

        #self.send_to_liquidity(transactions_infos['conta_id'], transactions_infos['valor'])


    def change_transaction_status(self, status): # PROBLEMA DE LOGICA AQUI -> CORRIGIR
        self.conn.execute('UPDATE transactions SET transaction_status=? WHERE id=?', (status['transaction_status'], status['id'])) # Conta_id vai setar o status para todas as transações pendentes da conta, independente de quais sejam. Trocar para ID ao invés da chave de transferencia.
        self.conn.commit()


    def realize_transaction(self, destiny, value):

        self.cur.execute('UPDATE cryptabank SET currency=currency + ? WHERE account = ?;', (value, self.liquidity_id))
        self.cur.execute('UPDATE users SET currency=currency + ? WHERE conta_id=?;', (value * (-1), destiny))



    def get_currency_infos(self, infos):
        consulta = self.cur.execute('SELECT currency FROM users WHERE conta_id=? OR email=?', (infos['conta_id'], infos['email'])).fetchone()
        return dict(consulta)
    

    def account_exists(self, account_id):
        consulta = self.cur.execute('SELECT * FROM users WHERE conta_id=?', (account_id,)).fetchone()
        if consulta:
            return True
        return False
    

    def set_warning(self, conta_id, warning, info):
        self.cur.execute('INSERT INTO warning_list(warning_to, warning, info) VALUES(?, ?, ?)', (conta_id, warning, info))


    def get_all_warnings(self, conta_id):
        consulta = self.cur.execute('SELECT * FROM warning_list WHERE warning_to=?;', (conta_id,)).fetchall()
        self.cur.execute('DELETE FROM warning_list WHERE warning_to=?', (conta_id,))

        return [dict(row) for row in consulta]


    #DEV

    def get_all_transactions(self):
        consulta = self.cur.execute('SELECT * FROM transactions;').fetchall()
        return [dict(row) for row in consulta]
    

    def get_all_users(self):
        consulta = self.cur.execute('SELECT * FROM users').fetchall()
        return [dict(row) for row in consulta]

    def set_currency(self, valor, email):
        self.conn.execute('UPDATE users SET currency=? WHERE email=?;', (valor, email))
        self.conn.commit()


