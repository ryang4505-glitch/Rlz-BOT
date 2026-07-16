"""
database.py
------------
Responsável por:
  - Abrir conexões com o banco SQLite.
  - Criar o schema (tabelas) caso não exista.
  - Sincronizar os administradores definidos no .env com a tabela `admins`.

O banco inicia sempre vazio de dados de negócio (produtos, categorias,
promoções, pedidos, etc). A única sincronização automática é a lista de
administradores, pois ela vem de uma configuração real (.env), não de
dados fictícios.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER UNIQUE NOT NULL,
    name          TEXT,
    added_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER UNIQUE NOT NULL,
    username      TEXT,
    first_name    TEXT,
    last_name     TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    description   TEXT,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id       INTEGER NOT NULL,
    name              TEXT NOT NULL,
    description       TEXT,
    price             REAL NOT NULL,
    delivery_type     TEXT NOT NULL,   -- arquivo, link, texto, codigo, licenca, convite
    delivery_content  TEXT,
    active            INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_photos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL,
    file_id       TEXT NOT NULL,
    media_type    TEXT NOT NULL DEFAULT 'photo',
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS promotions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    text              TEXT NOT NULL,
    image_file_id     TEXT,
    media_type        TEXT NOT NULL DEFAULT 'photo',
    product_id        INTEGER,
    interval_minutes  INTEGER NOT NULL,
    active            INTEGER NOT NULL DEFAULT 0,
    target_group_ids  TEXT,
    created_at        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS groups (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id       INTEGER UNIQUE NOT NULL,
    title         TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending, authorized, blocked
    added_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    price         REAL NOT NULL,
    status        TEXT NOT NULL DEFAULT 'aguardando_pagamento',
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    proof_file_id   TEXT,
    proof_type      TEXT,
    submitted_at    TEXT DEFAULT (datetime('now')),
    reviewed_by     INTEGER,
    reviewed_at     TEXT,
    status          TEXT NOT NULL DEFAULT 'pendente',  -- pendente, aprovado, recusado
    FOREIGN KEY (order_id) REFERENCES orders (id)
);

CREATE TABLE IF NOT EXISTS settings (
    key     TEXT PRIMARY KEY,
    value   TEXT
);
"""


def _ensure_db_dir() -> None:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Retorna uma nova conexão SQLite com row_factory configurado."""
    _ensure_db_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit: bool = False):
    """Context manager que entrega um cursor e fecha a conexão automaticamente."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Cria as tabelas (se não existirem), aplica migrações leves e sincroniza os admins do .env."""
    _ensure_db_dir()
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
        _run_migrations(conn)
        _sync_admins_from_env(conn)
    finally:
        conn.close()


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Aplica pequenas alterações de schema em bancos criados por versões anteriores."""
    cur = conn.execute("PRAGMA table_info(product_photos)")
    photo_columns = {row["name"] for row in cur.fetchall()}
    if "media_type" not in photo_columns:
        conn.execute("ALTER TABLE product_photos ADD COLUMN media_type TEXT NOT NULL DEFAULT 'photo'")
        conn.commit()

    cur = conn.execute("PRAGMA table_info(promotions)")
    promo_columns = {row["name"] for row in cur.fetchall()}
    if "media_type" not in promo_columns:
        conn.execute("ALTER TABLE promotions ADD COLUMN media_type TEXT NOT NULL DEFAULT 'photo'")
        conn.commit()
    if "target_group_ids" not in promo_columns:
        conn.execute("ALTER TABLE promotions ADD COLUMN target_group_ids TEXT")
        conn.commit()


def _sync_admins_from_env(conn: sqlite3.Connection) -> None:
    """Garante que todo ID presente em ADMIN_IDS (.env) exista na tabela admins."""
    for admin_id in config.ADMIN_IDS:
        conn.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, name) VALUES (?, ?)",
            (admin_id, None),
        )
    conn.commit()
