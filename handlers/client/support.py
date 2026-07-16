"""Handlers do atendimento/suporte automático."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import config
import database
from services import customer_service
from utils import keyboards

logger = logging.getLogger("shop_bot.client.support")


async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'support:start' — inicia a coleta da mensagem de suporte."""
    query = update.callback_query
    await query.answer()

    context.user_data["flow"] = {"type": "support_message"}

    await query.edit_message_text(
        "💬 Digite sua dúvida ou mensagem que iremos repassar para a nossa equipe de suporte.",
        reply_markup=keyboards.back_to_menu_button(),
    )


async def handle_support_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    """Recebe o texto da mensagem de suporte e encaminha aos administradores."""
    message_text = update.message.text
    user = update.effective_user
    customer_service.get_or_create_customer(
        telegram_id=user.id, username=user.username,
        first_name=user.first_name, last_name=user.last_name,
    )

    context.user_data.pop("flow", None)

    username = f"@{user.username}" if user.username else "(sem username)"
    admin_text = (
        f"💬 *Nova mensagem de suporte*\n\n"
        f"👤 {user.first_name} {username}\n"
        f"🆔 `{user.id}`\n\n"
        f"Mensagem:\n{message_text}"
    )

    admin_ids = set(config.ADMIN_IDS)
    with database.get_cursor() as cur:
        cur.execute("SELECT telegram_id FROM admins")
        for row in cur.fetchall():
            admin_ids.add(row["telegram_id"])

    for admin_id in admin_ids:
        try:
            await context.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            logger.exception("Falha ao encaminhar mensagem de suporte ao admin %s", admin_id)

    await update.message.reply_text(
        "✅ Sua mensagem foi enviada ao suporte. Em breve entraremos em contato!",
        reply_markup=keyboards.back_to_menu_button(),
    )
