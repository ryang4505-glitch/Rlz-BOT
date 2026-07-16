"""Representação tipada de um cliente do bot."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Customer":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            created_at=row["created_at"],
        )
