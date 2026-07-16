"""Regras de negócio (CRUD) para categorias de produtos."""

from typing import Optional

import database
from models.category import Category


def create(name: str, description: Optional[str]) -> Category:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description),
        )
        cur.execute("SELECT * FROM categories WHERE id = ?", (cur.lastrowid,))
        return Category.from_row(cur.fetchone())


def get_by_id(category_id: int) -> Optional[Category]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return Category.from_row(row) if row else None


def list_all(only_active: bool = False) -> list[Category]:
    with database.get_cursor() as cur:
        if only_active:
            cur.execute("SELECT * FROM categories WHERE active = 1 ORDER BY name")
        else:
            cur.execute("SELECT * FROM categories ORDER BY name")
        return [Category.from_row(r) for r in cur.fetchall()]


def update_name(category_id: int, name: str) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))


def update_description(category_id: int, description: str) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("UPDATE categories SET description = ? WHERE id = ?", (description, category_id))


def toggle_active(category_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("SELECT active FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        if row:
            new_value = 0 if row["active"] else 1
            cur.execute("UPDATE categories SET active = ? WHERE id = ?", (new_value, category_id))


def delete(category_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def has_products(category_id: int) -> bool:
    with database.get_cursor() as cur:
        cur.execute("SELECT 1 FROM products WHERE category_id = ? LIMIT 1", (category_id,))
        return cur.fetchone() is not None
