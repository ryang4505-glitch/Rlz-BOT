"""Decorators reutilizáveis para handlers do bot."""

import functools
import logging

from telegram import Update
from telegram.ext import ContextTypes

from services import admin_service

logger = logging.getLogger("shop_bot.decorators")


def admin_only(handler_func):
    """Garante que somente administradores autorizados executem o handler."""

    @functools.wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or not admin_service.is_admin(user.id):
            logger.warning("Acesso negado ao painel administrativo: user_id=%s", user and user.id)
            if update.callback_query:
                await update.callback_query.answer("🚫 Você não tem permissão para isso.", show_alert=True)
            elif update.message:
                await update.message.reply_text("🚫 Você não tem permissão para acessar o painel administrativo.")
            return None
        return await handler_func(update, context, *args, **kwargs)

    return wrapper
