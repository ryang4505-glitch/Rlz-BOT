"""Handler de entrada do painel administrativo (/painel e /admin)."""

from telegram import Update
from telegram.ext import ContextTypes

from utils.decorators import admin_only
from utils import keyboards

PANEL_TEXT = "🛠 *Painel Administrativo*\n\nEscolha uma opção:"


@admin_only
async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /painel (ou /admin) — abre o painel administrativo."""
    context.user_data.pop("flow", None)
    await update.message.reply_text(
        PANEL_TEXT, parse_mode="Markdown", reply_markup=keyboards.admin_main_menu()
    )


@admin_only
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'adm:menu' — volta para o menu principal do painel."""
    query = update.callback_query
    await query.answer()
    context.user_data.pop("flow", None)
    await query.edit_message_text(PANEL_TEXT, parse_mode="Markdown", reply_markup=keyboards.admin_main_menu())


@admin_only
async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'adm:cancel' — cancela qualquer fluxo em andamento e volta ao menu."""
    query = update.callback_query
    await query.answer("Operação cancelada.")
    context.user_data.pop("flow", None)
    await query.edit_message_text(PANEL_TEXT, parse_mode="Markdown", reply_markup=keyboards.admin_main_menu())
