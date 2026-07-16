"""Leitura e escrita de configurações genéricas (tabela key/value settings)."""

from typing import Optional

import database


def get(key: str, default: Optional[str] = None) -> Optional[str]:
    with database.get_cursor() as cur:
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default


def set(key: str, value: str) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
