"""Cálculo de estatísticas exibidas no painel administrativo."""

from dataclasses import dataclass

import database
from services import customer_service, product_service, order_service, group_service
from utils import constants


@dataclass
class ShopStats:
    total_customers: int
    total_products: int
    total_orders: int
    orders_pending_review: int
    total_groups: int
    authorized_groups: int
    approved_revenue: float


def build_stats() -> ShopStats:
    with database.get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as total FROM orders WHERE status = ?",
            (constants.ORDER_AGUARDANDO_APROVACAO,),
        )
        pending_review = cur.fetchone()["total"]

    groups = group_service.list_all()
    authorized = [g for g in groups if g.status == constants.GROUP_AUTHORIZED]

    return ShopStats(
        total_customers=customer_service.count_all(),
        total_products=product_service.count_all(),
        total_orders=order_service.count_all(),
        orders_pending_review=pending_review,
        total_groups=len(groups),
        authorized_groups=len(authorized),
        approved_revenue=order_service.sum_approved_revenue(),
    )
