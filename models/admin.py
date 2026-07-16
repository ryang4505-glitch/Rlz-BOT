"""Representação tipada de um administrador do bot."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Admin:
    id: int
    telegram_id: int
    name: Optional[str]
    added_at: str

    @classmethod
    def from_row(cls, row) -> "Admin":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            name=row["name"],
            added_at=row["added_at"],
        )
