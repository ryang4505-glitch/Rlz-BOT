"""Handler do botão '🔥 Promoções' no menu do cliente."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import promotion_service, product_service
from utils import keyboards


async def list_promotions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'promo:list' — mostra as promoções atualmente ativas."""
    query = update.callback_query
    await query.answer()

    promotions = promotion_service.list_active()
    if not promotions:
        await query.edit_message_text(
            "😕 Nenhuma promoção ativa no momento.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    rows = []
    for promo in promotions:
        label = f"🔥 {promo.name}"
        if promo.product_id:
            rows.append([InlineKeyboardButton(label, callback_data=f"prod:{promo.product_id}")])
        else:
            rows.append([InlineKeyboardButton(label, callback_data="promo:list")])
    rows.append([InlineKeyboardButton("⬅️ Menu inicial", callback_data="menu:main")])

    await query.edit_message_text(
        "🔥 *Promoções ativas:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(rows),
    )
