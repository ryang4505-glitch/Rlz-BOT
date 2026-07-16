"""Handlers do fluxo de compra: instruções de pagamento e envio de comprovante."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import config
import database
from services import (
    product_service,
    customer_service,
    order_service,
    payment_service,
    settings_service,
)
from utils import keyboards, constants

logger = logging.getLogger("shop_bot.client.purchase")


async def start_purchase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'buy:<product_id>' — ponto de entrada via botão."""
    query = update.callback_query
    data = query.data

    if data == "buy:cancel":
        await cancel_purchase(update, context)
        return

    await query.answer()
    product_id = int(data.split(":")[1])
    await start_purchase(update, context, product_id)


async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int) -> None:
    """Cria o pedido e envia as instruções de pagamento via Pix ao cliente."""
    chat_id = update.effective_chat.id
    user = update.effective_user

    product = product_service.get_by_id(product_id)
    if product is None or not product.active:
        await context.bot.send_message(chat_id, "😕 Esse produto não está mais disponível.",
                                         reply_markup=keyboards.back_to_menu_button())
        return

    pix_key = settings_service.get(constants.SETTING_PIX_KEY)
    if not pix_key:
        await context.bot.send_message(
            chat_id,
            "⚠️ No momento os pagamentos estão indisponíveis. Contate o suporte.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    customer = customer_service.get_or_create_customer(
        telegram_id=user.id, username=user.username,
        first_name=user.first_name, last_name=user.last_name,
    )
    order = order_service.create(customer_id=customer.id, product_id=product.id, price=product.price)

    pix_name = settings_service.get(constants.SETTING_PIX_NAME)
    pix_line = f"🔑 Chave Pix: `{pix_key}`"
    if pix_name:
        pix_line += f"\n👤 Titular: {pix_name}"

    text = (
        f"🛒 *Pedido #{order.id} criado!*\n\n"
        f"📦 Produto: *{product.name}*\n"
        f"💰 Valor: *R$ {product.price:.2f}*\n\n"
        f"{pix_line}\n\n"
        "Após realizar o pagamento, envie a *foto ou o arquivo do comprovante* aqui nesta conversa."
    )

    context.user_data["purchase"] = {"order_id": order.id}

    await context.bot.send_message(
        chat_id, text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.pix_payment_keyboard(pix_key),
    )


async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Compra cancelada.")

    purchase_state = context.user_data.pop("purchase", None)
    if purchase_state:
        order_service.set_status(purchase_state["order_id"], constants.ORDER_RECUSADO)

    await query.edit_message_text("❌ Compra cancelada.", reply_markup=keyboards.back_to_menu_button())


async def handle_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe a foto/arquivo do comprovante enviado pelo cliente."""
    purchase_state = context.user_data.get("purchase")
    if not purchase_state:
        return

    order_id = purchase_state["order_id"]
    order = order_service.get_by_id(order_id)
    if order is None or order.status != constants.ORDER_AGUARDANDO_PAGAMENTO:
        context.user_data.pop("purchase", None)
        await update.message.reply_text("⚠️ Esse pedido não está mais aguardando pagamento.")
        return

    message = update.message
    if message.photo:
        file_id = message.photo[-1].file_id
        proof_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        proof_type = "document"
    else:
        await message.reply_text("⚠️ Envie o comprovante como foto ou arquivo.")
        return

    payment_service.create(order_id=order.id, proof_file_id=file_id, proof_type=proof_type)
    order_service.set_status(order.id, constants.ORDER_AGUARDANDO_APROVACAO)
    context.user_data.pop("purchase", None)

    await message.reply_text(
        "✅ Comprovante recebido! Assim que for analisado você será notificado aqui.",
        reply_markup=keyboards.back_to_menu_button(),
    )

    await _notify_admins_new_payment(context, order, proof_type, file_id)


async def _notify_admins_new_payment(context: ContextTypes.DEFAULT_TYPE, order, proof_type: str, file_id: str) -> None:
    customer = customer_service.get_by_id(order.customer_id)
    product = product_service.get_by_id(order.product_id)

    username = f"@{customer.username}" if customer and customer.username else "(sem username)"
    caption = (
        f"🧾 *Novo comprovante recebido!*\n\n"
        f"👤 Cliente: {customer.first_name if customer else '?'} {username}\n"
        f"🆔 Telegram ID: `{customer.telegram_id if customer else '?'}`\n"
        f"📦 Produto: {product.name if product else '?'}\n"
        f"💰 Valor: R$ {order.price:.2f}\n"
        f"🧾 Pedido: #{order.id}"
    )

    admin_ids = set(config.ADMIN_IDS)
    with database.get_cursor() as cur:
        cur.execute("SELECT telegram_id FROM admins")
        for row in cur.fetchall():
            admin_ids.add(row["telegram_id"])

    keyboard = keyboards.admin_order_detail_keyboard(order.id)

    for admin_id in admin_ids:
        try:
            if proof_type == "photo":
                await context.bot.send_photo(admin_id, file_id, caption=caption,
                                              parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            else:
                await context.bot.send_document(admin_id, file_id, caption=caption,
                                                 parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        except Exception:
            logger.exception("Falha ao notificar admin %s sobre o pedido %s", admin_id, order.id)
