"""Regras de negócio relacionadas ao envio e análise de comprovantes de pagamento."""

from typing import Optional

import database
from models.order import Payment
from utils import constants


def create(order_id: int, proof_file_id: str, proof_type: str) -> Payment:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO payments (order_id, proof_file_id, proof_type, status)
               VALUES (?, ?, ?, ?)""",
            (order_id, proof_file_id, proof_type, constants.PAYMENT_PENDENTE),
        )
        cur.execute("SELECT * FROM payments WHERE id = ?", (cur.lastrowid,))
        return Payment.from_row(cur.fetchone())


def get_latest_by_order(order_id: int) -> Optional[Payment]:
    with database.get_cursor() as cur:
        cur.execute(
            "SELECT * FROM payments WHERE order_id = ? ORDER BY submitted_at DESC LIMIT 1",
            (order_id,),
        )
        row = cur.fetchone()
        return Payment.from_row(row) if row else None


def review(payment_id: int, approved: bool, reviewed_by: int) -> None:
    status = constants.PAYMENT_APROVADO if approved else constants.PAYMENT_RECUSADO
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            """UPDATE payments
               SET status = ?, reviewed_by = ?, reviewed_at = datetime('now')
               WHERE id = ?""",
            (status, reviewed_by, payment_id),
        )
