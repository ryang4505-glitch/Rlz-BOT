"""Handlers administrativos para autorizar, bloquear e remover grupos."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import group_service
from utils import keyboards, constants
from utils.decorators import admin_only


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    groups = group_service.list_all()
    if not groups:
        await query.edit_message_text(
            "👥 Nenhum grupo detectado ainda.\n\nAdicione o bot a um grupo para que ele apareça aqui.",
            reply_markup=keyboards.admin_back_button(),
        )
        return
    await query.edit_message_text("👥 *Grupos*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_groups_menu(groups))


async def _render_group_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int) -> None:
    group = group_service.get_by_id(group_id)
    if group is None:
        await update.callback_query.edit_message_text("⚠️ Grupo não encontrado.",
                                                        reply_markup=keyboards.admin_back_button())
        return
    text = (
        f"👥 *{group.title or '(sem título)'}*\n\n"
        f"ID: `{group.chat_id}`\n"
        f"Status: {constants.GROUP_STATUS_LABELS.get(group.status, group.status)}\n"
        f"Detectado em: {group.added_at}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_group_detail_keyboard(group)
    )


@admin_only
async def view_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split(":")[-1])
    await _render_group_detail(update, context, group_id)


@admin_only
async def authorize_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    group_id = int(query.data.split(":")[-1])
    group_service.set_status(group_id, constants.GROUP_AUTHORIZED)
    await query.answer("Grupo autorizado!")
    await _render_group_detail(update, context, group_id)


@admin_only
async def block_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    group_id = int(query.data.split(":")[-1])
    group_service.set_status(group_id, constants.GROUP_BLOCKED)
    await query.answer("Grupo bloqueado.")
    await _render_group_detail(update, context, group_id)


@admin_only
async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    group_id = int(query.data.split(":")[-1])
    group_service.remove(group_id)
    await query.answer("Grupo removido.")
    await menu(update, context)
