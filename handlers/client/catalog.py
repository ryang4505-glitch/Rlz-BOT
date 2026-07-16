"""Handlers de navegação do cliente pelo catálogo de produtos."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import category_service, product_service
from utils import keyboards

logger = logging.getLogger("shop_bot.client.catalog")


async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'cat:list' — mostra todas as categorias ativas."""
    query = update.callback_query
    await query.answer()

    categories = category_service.list_all(only_active=True)
    if not categories:
        await query.edit_message_text(
            "😕 Nenhuma categoria disponível no momento. Volte mais tarde!",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    await query.edit_message_text(
        "🛒 Escolha uma categoria:",
        reply_markup=keyboards.categories_keyboard(categories),
    )


async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'cat:<id>' — lista os produtos de uma categoria."""
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split(":")[1])
    category = category_service.get_by_id(category_id)
    if category is None or not category.active:
        await query.edit_message_text(
            "😕 Essa categoria não está mais disponível.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    products = product_service.list_by_category(category_id, only_active=True)
    if not products:
        await query.edit_message_text(
            f"😕 Nenhum produto disponível em *{category.name}* no momento.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboards.categories_keyboard(category_service.list_all(only_active=True)),
        )
        return

    await query.edit_message_text(
        f"🛍 Produtos em *{category.name}*:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.products_keyboard(products, category_id),
    )


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback 'prod:<id>' — mostra os detalhes de um produto."""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split(":")[1])
    product = product_service.get_by_id(product_id)
    if product is None or not product.active:
        await query.edit_message_text(
            "😕 Esse produto não está mais disponível.",
            reply_markup=keyboards.back_to_menu_button(),
        )
        return

    caption = (
        f"🛍 *{product.name}*\n\n"
        f"{product.description or ''}\n\n"
        f"💰 Preço: *R$ {product.price:.2f}*"
    )
    keyboard = keyboards.product_detail_keyboard(product.id, product.category_id)

    photos = product_service.list_photos(product.id)
    if photos:
        try:
            await query.message.delete()
        except Exception:
            pass
        first = photos[0]
        if first.media_type == "video":
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=first.file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=first.file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    else:
        await query.edit_message_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
