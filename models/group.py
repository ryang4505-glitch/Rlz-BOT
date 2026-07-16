"""Representação tipada de um grupo/canal onde o bot está presente."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Group:
    id: int
    chat_id: int
    title: Optional[str]
    status: str  # pending, authorized, blocked
    added_at: str

    @classmethod
    def from_row(cls, row) -> "Group":
        return cls(
            id=row["id"],
            chat_id=row["chat_id"],
            title=row["title"],
            status=row["status"],
            added_at=row["added_at"],
        )
