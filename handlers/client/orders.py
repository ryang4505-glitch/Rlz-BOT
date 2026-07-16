"""Handlers para o cliente acompanhar seus próprios pedidos."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import customer_service, order_service, product_service
from utils import keyboards, constants


async def list_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'orders:list' — lista os pedidos do cliente."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    customer = customer_service.get_by_telegram_id(user.id)
    if not customer:
        await query.edit_message_text(
            "📦 Você ainda não fez nenhum pedido.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    orders = order_service.list_by_customer(customer.id)
    if not orders:
        await query.edit_message_text(
            "📦 Você ainda não fez nenhum pedido.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    await query.edit_message_text(
        "📦 Seus pedidos:",
        reply_markup=keyboards.orders_keyboard(orders),
    )


async def show_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'order:<id>' — mostra detalhes de um pedido específico."""
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split(":")[1])
    order = order_service.get_by_id(order_id)

    user = update.effective_user
    customer = customer_service.get_by_telegram_id(user.id)

    if order is None or customer is None or order.customer_id != customer.id:
        await query.edit_message_text(
            "⚠️ Pedido não encontrado.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    product = product_service.get_by_id(order.product_id)
    status_label = constants.ORDER_STATUS_LABELS.get(order.status, order.status)

    text = (
        f"🧾 *Pedido #{order.id}*\n\n"
        f"📦 Produto: {product.name if product else '(produto removido)'}\n"
        f"💰 Valor: R$ {order.price:.2f}\n"
        f"📌 Status: {status_label}\n"
        f"🗓 Criado em: {order.created_at}"
    )

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.back_to_menu_button())
