"""Representação tipada de uma promoção de divulgação automática."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Promotion:
    id: int
    name: str
    text: str
    image_file_id: Optional[str]
    media_type: str  # 'photo' ou 'video'
    product_id: Optional[int]
    interval_minutes: int
    active: bool
    target_group_ids: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Promotion":
        return cls(
            id=row["id"],
            name=row["name"],
            text=row["text"],
            image_file_id=row["image_file_id"],
            media_type=row["media_type"] if "media_type" in row.keys() else "photo",
            product_id=row["product_id"],
            interval_minutes=row["interval_minutes"],
            active=bool(row["active"]),
            target_group_ids=row["target_group_ids"] if "target_group_ids" in row.keys() else None,
            created_at=row["created_at"],
        )

    def target_group_id_list(self) -> list[int]:
        """Converte a string 'target_group_ids' (ex: '1,4,7') em lista de inteiros."""
        if not self.target_group_ids:
            return []
        return [int(x) for x in self.target_group_ids.split(",") if x.strip().isdigit()]
