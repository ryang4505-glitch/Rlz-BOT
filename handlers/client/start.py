"""Handler do comando /start e do menu principal do cliente."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services import customer_service
from utils import keyboards

logger = logging.getLogger("shop_bot.client.start")

WELCOME_TEXT = (
    "👋 Olá, {first_name}!\n\n"
    "Bem-vindo(a) à nossa loja digital.\n"
    "Use os botões abaixo para navegar:"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ponto de entrada /start. Registra o cliente e mostra o menu principal.

    Também trata deep links de divulgação (?start=buy_<product_id>) vindos
    dos botões de promoção enviados nos grupos.
    """
    user = update.effective_user
    customer_service.get_or_create_customer(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await update.message.reply_text(
        WELCOME_TEXT.format(first_name=user.first_name or "cliente"),
        reply_markup=keyboards.client_main_menu(),
    )

    if context.args:
        param = context.args[0]
        if param.startswith("buy_"):
            product_id_raw = param.removeprefix("buy_")
            if product_id_raw.isdigit():
                # Import local para evitar dependência circular no carregamento do módulo
                from handlers.client import purchase
                await purchase.start_purchase(update, context, int(product_id_raw))


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'menu:main' — volta para o menu inicial."""
    query = update.callback_query
    await query.answer()
    context.user_data.pop("flow", None)
    context.user_data.pop("purchase", None)
    user = update.effective_user
    await query.edit_message_text(
        WELCOME_TEXT.format(first_name=user.first_name or "cliente"),
        reply_markup=keyboards.client_main_menu(),
    )
