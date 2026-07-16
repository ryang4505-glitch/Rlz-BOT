"""Representação tipada de pedidos e pagamentos."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    id: int
    customer_id: int
    product_id: int
    price: float
    status: str  # aguardando_pagamento, aguardando_aprovacao, aprovado, recusado, entregue
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Order":
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            product_id=row["product_id"],
            price=row["price"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class Payment:
    id: int
    order_id: int
    proof_file_id: Optional[str]
    proof_type: Optional[str]
    submitted_at: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[str]
    status: str  # pendente, aprovado, recusado

    @classmethod
    def from_row(cls, row) -> "Payment":
        return cls(
            id=row["id"],
            order_id=row["order_id"],
            proof_file_id=row["proof_file_id"],
            proof_type=row["proof_type"],
            submitted_at=row["submitted_at"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=row["reviewed_at"],
            status=row["status"],
        )
