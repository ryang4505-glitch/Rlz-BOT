"""Handlers administrativos para configuração da chave Pix."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import settings_service
from utils import keyboards, constants
from utils.decorators import admin_only


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    pix_key = settings_service.get(constants.SETTING_PIX_KEY)
    pix_name = settings_service.get(constants.SETTING_PIX_NAME)

    if pix_key:
        text = f"💠 *Configuração Pix*\n\n🔑 Chave: `{pix_key}`\n👤 Titular: {pix_name or '(não informado)'}"
    else:
        text = "💠 *Configuração Pix*\n\n⚠️ Nenhuma chave Pix configurada ainda."

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Configurar Pix", callback_data="adm:pix:edit")],
        [keyboards.admin_back_button()],
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


@admin_only
async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["flow"] = {"type": "pix_set", "step": "key", "data": {}}
    await query.edit_message_text("Digite a *chave Pix*:", parse_mode=ParseMode.MARKDOWN)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    step = flow["step"]
    text = update.message.text.strip()

    if step == "key":
        if not text:
            await update.message.reply_text("⚠️ A chave Pix não pode ficar vazia.")
            return
        flow["data"]["key"] = text
        flow["step"] = "name"
        await update.message.reply_text(
            "Digite o *nome do titular* da chave Pix (envie '-' para pular):", parse_mode=ParseMode.MARKDOWN
        )
        return

    if step == "name":
        name = None if text == "-" else text
        settings_service.set(constants.SETTING_PIX_KEY, flow["data"]["key"])
        if name:
            settings_service.set(constants.SETTING_PIX_NAME, name)
        context.user_data.pop("flow", None)
        await update.message.reply_text("✅ Chave Pix configurada com sucesso!",
                                         reply_markup=keyboards.admin_main_menu())
        return
