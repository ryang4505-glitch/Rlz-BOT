"""Handlers administrativos para visualizar pedidos e aprovar/recusar pagamentos."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import (
    order_service,
    payment_service,
    customer_service,
    product_service,
    delivery_service,
)
from utils import keyboards, constants
from utils.decorators import admin_only

logger = logging.getLogger("shop_bot.admin.orders")


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    orders = order_service.list_all()
    if not orders:
        await query.edit_message_text("🧾 Nenhum pedido registrado ainda.",
                                       reply_markup=keyboards.admin_back_button())
        return
    await query.edit_message_text("🧾 *Pedidos:*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_orders_list_keyboard(orders))


@admin_only
async def view_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split(":")[-1])
    await _render_order_detail(update, context, order_id)


async def _render_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int) -> None:
    order = order_service.get_by_id(order_id)
    if order is None:
        await update.callback_query.edit_message_text("⚠️ Pedido não encontrado.",
                                                        reply_markup=keyboards.admin_back_button())
        return

    customer = customer_service.get_by_id(order.customer_id)
    product = product_service.get_by_id(order.product_id)
    username = f"@{customer.username}" if customer and customer.username else "(sem username)"

    text = (
        f"🧾 *Pedido #{order.id}*\n\n"
        f"👤 Cliente: {customer.first_name if customer else '?'} {username}\n"
        f"🆔 Telegram ID: `{customer.telegram_id if customer else '?'}`\n"
        f"📦 Produto: {product.name if product else '(removido)'}\n"
        f"💰 Valor: R$ {order.price:.2f}\n"
        f"📌 Status: {constants.ORDER_STATUS_LABELS.get(order.status, order.status)}\n"
        f"🗓 Criado em: {order.created_at}"
    )

    keyboard = None
    if order.status == constants.ORDER_AGUARDANDO_APROVACAO:
        keyboard = keyboards.admin_order_detail_keyboard(order.id)
    else:
        keyboard = keyboards.admin_back_button("adm:orders")

    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


@admin_only
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    order_id = int(query.data.split(":")[-1])
    order = order_service.get_by_id(order_id)
    if order is None:
        await query.answer("Pedido não encontrado.")
        return

    payment = payment_service.get_latest_by_order(order_id)
    if payment is None:
        await query.answer("Nenhum comprovante encontrado para este pedido.")
        return

    admin_user = update.effective_user
    payment_service.review(payment.id, approved=True, reviewed_by=admin_user.id)
    order_service.set_status(order_id, constants.ORDER_APROVADO)

    customer = customer_service.get_by_id(order.customer_id)
    product = product_service.get_by_id(order.product_id)

    if customer and product:
        try:
            await delivery_service.deliver_product(context.bot, customer, product)
            order_service.set_status(order_id, constants.ORDER_ENTREGUE)
        except Exception:
            logger.exception("Falha ao entregar produto do pedido %s", order_id)
            await context.bot.send_message(
                customer.telegram_id,
                "✅ Pagamento aprovado! Houve um problema técnico na entrega automática, "
                "nossa equipe irá lhe atender em breve.",
            )

    await query.answer("Pagamento aprovado!")
    await _render_order_detail(update, context, order_id)


@admin_only
async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    order_id = int(query.data.split(":")[-1])
    order = order_service.get_by_id(order_id)
    if order is None:
        await query.answer("Pedido não encontrado.")
        return

    payment = payment_service.get_latest_by_order(order_id)
    admin_user = update.effective_user
    if payment:
        payment_service.review(payment.id, approved=False, reviewed_by=admin_user.id)
    order_service.set_status(order_id, constants.ORDER_RECUSADO)

    customer = customer_service.get_by_id(order.customer_id)
    if customer:
        try:
            await context.bot.send_message(
                customer.telegram_id,
                "❌ Seu comprovante de pagamento foi recusado. Entre em contato com o suporte para mais informações.",
            )
        except Exception:
            logger.exception("Falha ao notificar cliente sobre recusa do pedido %s", order_id)

    await query.answer("Pagamento recusado.")
    await _render_order_detail(update, context, order_id)
