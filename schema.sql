CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    conta_id TEXT UNIQUE,
    created_at TEXT,
    bloqueado INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel INTEGER NOT NULL DEFAULT 0, -- 0 = suporte, 1 = admin
    email TEXT UNIQUE,
    senha TEXT,
    nome TEXT
);

CREATE TABLE IF NOT EXISTS users_cookies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    cookie TEXT
);

CREATE TABLE IF NOT EXISTS admin_cookies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    cookie TEXT
);

CREATE TABLE IF NOT EXISTS mensagens_suporte(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enviado_em DATE DEFAULT CURRENT_TIMESTAMP,
    email TEXT,
    categoria TEXT,
    assunto TEXT,
    problema TEXT,
    status TEXT DEFAULT 'aberto',
    resposta TEXT
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

-- Conta padrao de admin (nivel=1 = admin completo)
-- Email: admin@cryptabank.com | Senha: admin123
INSERT OR IGNORE INTO admins(nivel, email, senha, nome)
    VALUES (1, 'admin@cryptabank.com', 'admin123', 'Administrador');

INSERT OR IGNORE INTO admin_cookies(email, cookie)
    VALUES ('admin@cryptabank.com', 'c27a5d72dc674f5480f90008c9789415');
