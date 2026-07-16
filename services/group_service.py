"""Regras de negócio relacionadas aos grupos/canais em que o bot está presente."""

from typing import Optional

import database
from models.group import Group
from utils import constants


def register_or_update(chat_id: int, title: Optional[str]) -> Group:
    """Registra um grupo novo (status pendente) ou apenas atualiza o título se já existir."""
    with database.get_cursor(commit=True) as cur:
        cur.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE groups SET title = ? WHERE chat_id = ?", (title, chat_id))
            cur.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
            return Group.from_row(cur.fetchone())

        cur.execute(
            "INSERT INTO groups (chat_id, title, status) VALUES (?, ?, ?)",
            (chat_id, title, constants.GROUP_PENDING),
        )
        cur.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        return Group.from_row(cur.fetchone())


def get_by_id(group_id: int) -> Optional[Group]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
        row = cur.fetchone()
        return Group.from_row(row) if row else None


def list_all() -> list[Group]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM groups ORDER BY added_at DESC")
        return [Group.from_row(r) for r in cur.fetchall()]


def list_authorized() -> list[Group]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM groups WHERE status = ?", (constants.GROUP_AUTHORIZED,))
        return [Group.from_row(r) for r in cur.fetchall()]


def set_status(group_id: int, status: str) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("UPDATE groups SET status = ? WHERE id = ?", (status, group_id))


def remove(group_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM groups WHERE id = ?", (group_id,))
