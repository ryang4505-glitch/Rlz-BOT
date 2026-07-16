"""Regras de negócio (CRUD) para promoções de divulgação automática."""

from typing import Optional

import database
from models.promotion import Promotion


def create(name: str, text: str, image_file_id: Optional[str],
           product_id: Optional[int], interval_minutes: int, media_type: str = "photo",
           target_group_ids: Optional[str] = None) -> Promotion:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO promotions
               (name, text, image_file_id, media_type, product_id, interval_minutes, active, target_group_ids)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
            (name, text, image_file_id, media_type, product_id, interval_minutes, target_group_ids),
        )
        cur.execute("SELECT * FROM promotions WHERE id = ?", (cur.lastrowid,))
        return Promotion.from_row(cur.fetchone())


def get_by_id(promotion_id: int) -> Optional[Promotion]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM promotions WHERE id = ?", (promotion_id,))
        row = cur.fetchone()
        return Promotion.from_row(row) if row else None


def list_all() -> list[Promotion]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM promotions ORDER BY created_at DESC")
        return [Promotion.from_row(r) for r in cur.fetchall()]


def list_active() -> list[Promotion]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM promotions WHERE active = 1")
        return [Promotion.from_row(r) for r in cur.fetchall()]


def set_active(promotion_id: int, active: bool) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("UPDATE promotions SET active = ? WHERE id = ?", (1 if active else 0, promotion_id))


def delete(promotion_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM promotions WHERE id = ?", (promotion_id,))
