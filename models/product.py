"""Representação tipada de um produto e suas fotos."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    id: int
    category_id: int
    name: str
    description: Optional[str]
    price: float
    delivery_type: str        # arquivo, link, texto, codigo, licenca, convite
    delivery_content: Optional[str]
    active: bool
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Product":
        return cls(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            delivery_type=row["delivery_type"],
            delivery_content=row["delivery_content"],
            active=bool(row["active"]),
            created_at=row["created_at"],
        )


@dataclass
class ProductPhoto:
    id: int
    product_id: int
    file_id: str
    media_type: str  # 'photo' ou 'video'

    @classmethod
    def from_row(cls, row) -> "ProductPhoto":
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            file_id=row["file_id"],
            media_type=row["media_type"] if "media_type" in row.keys() else "photo",
        )
