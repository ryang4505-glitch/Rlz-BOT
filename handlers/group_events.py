"""Detecta automaticamente quando o bot é adicionado ou removido de um grupo/canal."""

import logging

from telegram import Update, ChatMember
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import config
import database
from services import group_service
from utils import constants, keyboards

logger = logging.getLogger("shop_bot.group_events")

_ACTIVE_STATUSES = {ChatMember.MEMBER, ChatMember.ADMINISTRATOR}
_INACTIVE_STATUSES = {ChatMember.LEFT, ChatMember.BANNED}


async def on_bot_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disparado sempre que o status do próprio bot muda em um chat (grupo/canal)."""
    result = update.my_chat_member
    if result is None:
        return

    chat = result.chat
    if chat.type not in ("group", "supergroup", "channel"):
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    was_active = old_status in _ACTIVE_STATUSES
    is_active = new_status in _ACTIVE_STATUSES

    if is_active and not was_active:
        group = group_service.register_or_update(chat.id, chat.title)
        logger.info("Bot adicionado ao grupo '%s' (%s) — status: %s", chat.title, chat.id, group.status)
        await _notify_admins_new_group(context, group.id, chat.title, chat.id)

    elif not is_active and was_active:
        existing = None
        with database.get_cursor() as cur:
            cur.execute("SELECT * FROM groups WHERE chat_id = ?", (chat.id,))
            existing = cur.fetchone()
        if existing:
            group_service.set_status(existing["id"], constants.GROUP_BLOCKED)
            logger.info("Bot removido do grupo '%s' (%s) — marcado como bloqueado.", chat.title, chat.id)


async def _notify_admins_new_group(context: ContextTypes.DEFAULT_TYPE, group_id: int, title: str, chat_id: int) -> None:
    text = (
        "👥 *Novo grupo detectado!*\n\n"
        f"Nome: {title}\n"
        f"ID: `{chat_id}`\n\n"
        "Autorize este grupo no painel para incluí-lo na divulgação automática."
    )

    admin_ids = set(config.ADMIN_IDS)
    with database.get_cursor() as cur:
        cur.execute("SELECT telegram_id FROM admins")
        for row in cur.fetchall():
            admin_ids.add(row["telegram_id"])

    group = group_service.get_by_id(group_id)
    keyboard = keyboards.admin_group_detail_keyboard(group) if group else None

    for admin_id in admin_ids:
        try:
            await context.bot.send_message(admin_id, text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        except Exception:
            logger.exception("Falha ao notificar admin %s sobre novo grupo", admin_id)
