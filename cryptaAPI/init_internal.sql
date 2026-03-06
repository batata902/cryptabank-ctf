CREATE TABLE IF NOT EXISTS cryptabank(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT UNIQUE,
    is_settlement INTEGER, -- 0 para Não, 1 para Sim
    currency INTEGER
);

INSERT INTO cryptabank (account, is_settlement, currency)
SELECT 'contadeliquidacaoxyz', 0, 0
WHERE NOT EXISTS (
    SELECT 1 
    FROM cryptabank 
    WHERE account = 'contadeliquidacaoxyz'
);

CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    conta_id TEXT UNIQUE,
    created_at TEXT,
    account_status TEXT, -- active = Operando normalmente // frozen = Congelada (Somente admin pode descongelar) // terminated = Desligada
    currency INTEGER
);

CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    source_currency INTEGER,
    destiny TEXT,
    quantity INTEGER,
    created_at DATE DEFAULT CURRENT_TIMESTAMP,
    transaction_status TEXT
);