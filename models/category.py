"""Representação tipada de uma categoria de produtos."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    description: Optional[str]
    active: bool
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Category":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            active=bool(row["active"]),
            created_at=row["created_at"],
        )
