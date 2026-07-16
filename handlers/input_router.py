"""
input_router.py
----------------
Roteia mensagens de texto, foto e documento para o handler correto,
com base no "flow" (fluxo com estado) armazenado em context.user_data.

Isso evita a necessidade de múltiplos ConversationHandlers aninhados,
mantendo um único ponto de entrada para entradas de texto/mídia livres.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.admin import products as admin_products
from handlers.admin import categories as admin_categories
from handlers.admin import promotions as admin_promotions
from handlers.admin import pix as admin_pix
from handlers.client import purchase as client_purchase
from handlers.client import support as client_support

logger = logging.getLogger("shop_bot.input_router")


async def route_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roteia mensagens de texto livres de acordo com o fluxo ativo do usuário."""
    flow = context.user_data.get("flow")
    if not flow:
        return  # Nenhum fluxo ativo — mensagem solta é ignorada silenciosamente.

    flow_type = flow.get("type")

    if flow_type == "product_add":
        await admin_products.handle_add_text(update, context, flow)
    elif flow_type == "product_edit_field":
        await admin_products.handle_edit_field_text(update, context, flow)
    elif flow_type == "product_edit_photos":
        await admin_products.handle_edit_photos(update, context, flow)
    elif flow_type == "product_edit_delivery_content":
        await admin_products.handle_edit_delivery_content_text(update, context, flow)
    elif flow_type == "category_add":
        await admin_categories.handle_add_text(update, context, flow)
    elif flow_type == "category_edit_name":
        await admin_categories.handle_edit_name_text(update, context, flow)
    elif flow_type == "category_edit_desc":
        await admin_categories.handle_edit_desc_text(update, context, flow)
    elif flow_type == "promotion_add":
        await admin_promotions.handle_add_text(update, context, flow)
    elif flow_type == "pix_set":
        await admin_pix.handle_text(update, context, flow)
    elif flow_type == "support_message":
        await client_support.handle_support_text(update, context, flow)
    else:
        logger.warning("Fluxo de texto desconhecido: %s", flow_type)


async def route_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roteia fotos/documentos de acordo com o fluxo ativo ou compra em andamento."""
    flow = context.user_data.get("flow")

    if flow:
        flow_type = flow.get("type")

        if flow_type == "product_add" and flow.get("step") == "delivery_file":
            await admin_products.handle_add_delivery_file(update, context, flow)
            return
        if flow_type == "product_add" and flow.get("step") == "photos":
            await admin_products.handle_add_photo(update, context, flow)
            return
        if flow_type == "product_edit_photos":
            await admin_products.handle_edit_photos(update, context, flow)
            return
        if flow_type == "product_edit_delivery_file":
            await admin_products.handle_edit_delivery_file(update, context, flow)
            return
        if flow_type == "promotion_add" and flow.get("step") == "image":
            await admin_promotions.handle_add_image(update, context, flow)
            return
        return

    if context.user_data.get("purchase"):
        await client_purchase.handle_proof(update, context)
        return
