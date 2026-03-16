CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    conta_id TEXT UNIQUE,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nick TEXT,
    nivel INTEGER, -- 0 é suporte, 1 é admin
    email TEXT UNIQUE,
    senha TEXT
);

CREATE TABLE IF NOT EXISTS users_cookies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    cookie TEXT
);

CREATE TABLE IF NOT EXISTS admin_cookies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cookie TEXT
);

CREATE TABLE IF NOT EXISTS mensagens_suporte(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enviado_em DATE DEFAULT CURRENT_TIMESTAMP,
    email TEXT,
    categoria TEXT,
    assunto TEXT,
    problema TEXT
);

CREATE TABLE IF NOT EXISTS transfer_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_wallet TEXT,
    destiny_wallet TEXT,
    valor INTEGER,
    dia DATE DEFAULT CURRENT_TIMESTAMP,
    transfer_status TEXT,
    descr TEXT
);


