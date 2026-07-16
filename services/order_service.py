"""Regras de negócio relacionadas a pedidos."""

from typing import Optional

import database
from models.order import Order
from utils import constants


def create(customer_id: int, product_id: int, price: float) -> Order:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO orders (customer_id, product_id, price, status) VALUES (?, ?, ?, ?)",
            (customer_id, product_id, price, constants.ORDER_AGUARDANDO_PAGAMENTO),
        )
        cur.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,))
        return Order.from_row(cur.fetchone())


def get_by_id(order_id: int) -> Optional[Order]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cur.fetchone()
        return Order.from_row(row) if row else None


def list_by_customer(customer_id: int) -> list[Order]:
    with database.get_cursor() as cur:
        cur.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        return [Order.from_row(r) for r in cur.fetchall()]


def list_pending_review() -> list[Order]:
    """Pedidos com comprovante enviado, aguardando aprovação do admin."""
    with database.get_cursor() as cur:
        cur.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY created_at ASC",
            (constants.ORDER_AGUARDANDO_APROVACAO,),
        )
        return [Order.from_row(r) for r in cur.fetchall()]


def list_all() -> list[Order]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        return [Order.from_row(r) for r in cur.fetchall()]


def set_status(order_id: int, status: str) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, order_id),
        )


def count_all() -> int:
    with database.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM orders")
        return cur.fetchone()["total"]


def sum_approved_revenue() -> float:
    with database.get_cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(price), 0) as total FROM orders WHERE status IN (?, ?)",
            (constants.ORDER_APROVADO, constants.ORDER_ENTREGUE),
        )
        return cur.fetchone()["total"]
