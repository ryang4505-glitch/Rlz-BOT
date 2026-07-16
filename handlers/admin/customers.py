"""Handler administrativo para visualizar clientes cadastrados."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import customer_service
from utils import keyboards
from utils.decorators import admin_only

MAX_LISTED = 30


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    customers = customer_service.list_all()
    total = len(customers)

    if not customers:
        await query.edit_message_text("🙋 Nenhum cliente cadastrado ainda.",
                                       reply_markup=keyboards.admin_back_button())
        return

    lines = [f"🙋 *Clientes* (total: {total})\n"]
    for customer in customers[:MAX_LISTED]:
        username = f"@{customer.username}" if customer.username else "(sem username)"
        lines.append(f"• {customer.first_name or ''} {username} — `{customer.telegram_id}`")

    if total > MAX_LISTED:
        lines.append(f"\n… e mais {total - MAX_LISTED} cliente(s).")

    await query.edit_message_text(
        "\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_back_button()
    )
