"""Regras de negócio relacionadas a clientes."""

from typing import Optional

import database
from models.customer import Customer


def get_or_create_customer(telegram_id: int, username: Optional[str],
                            first_name: Optional[str], last_name: Optional[str]) -> Customer:
    """Busca o cliente pelo telegram_id; cria automaticamente se ainda não existir."""
    with database.get_cursor(commit=True) as cur:
        cur.execute("SELECT * FROM customers WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            # Mantém username/nome atualizados
            cur.execute(
                "UPDATE customers SET username = ?, first_name = ?, last_name = ? WHERE telegram_id = ?",
                (username, first_name, last_name, telegram_id),
            )
            cur.execute("SELECT * FROM customers WHERE telegram_id = ?", (telegram_id,))
            row = cur.fetchone()
            return Customer.from_row(row)

        cur.execute(
            "INSERT INTO customers (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (telegram_id, username, first_name, last_name),
        )
        cur.execute("SELECT * FROM customers WHERE telegram_id = ?", (telegram_id,))
        return Customer.from_row(cur.fetchone())


def get_by_id(customer_id: int) -> Optional[Customer]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        return Customer.from_row(row) if row else None


def get_by_telegram_id(telegram_id: int) -> Optional[Customer]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return Customer.from_row(row) if row else None


def list_all() -> list[Customer]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM customers ORDER BY created_at DESC")
        return [Customer.from_row(r) for r in cur.fetchall()]


def count_all() -> int:
    with database.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM customers")
        return cur.fetchone()["total"]
