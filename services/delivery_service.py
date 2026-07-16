"""
delivery_service.py
--------------------
Responsável por entregar automaticamente o conteúdo digital de um produto
ao cliente, de acordo com o `delivery_type` configurado pelo administrador.
"""

import logging

from telegram import Bot
from telegram.constants import ParseMode

from models.product import Product
from models.customer import Customer
from utils import constants

logger = logging.getLogger("shop_bot.delivery")


async def deliver_product(bot: Bot, customer: Customer, product: Product) -> None:
    """Envia o conteúdo do produto ao cliente, conforme o tipo de entrega configurado."""
    chat_id = customer.telegram_id
    content = product.delivery_content or ""

    try:
        if product.delivery_type == constants.DELIVERY_ARQUIVO:
            await bot.send_document(
                chat_id=chat_id,
                document=content,
                caption=f"📦 Aqui está o seu produto: *{product.name}*",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif product.delivery_type == constants.DELIVERY_LINK:
            await bot.send_message(
                chat_id=chat_id,
                text=f"📦 Seu produto *{product.name}* está pronto!\n\n🔗 Link de acesso:\n{content}",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif product.delivery_type == constants.DELIVERY_TEXTO:
            await bot.send_message(
                chat_id=chat_id,
                text=f"📦 Seu produto *{product.name}*:\n\n{content}",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif product.delivery_type == constants.DELIVERY_CODIGO:
            await bot.send_message(
                chat_id=chat_id,
                text=f"📦 Seu produto *{product.name}*.\n\nCódigo:\n`{content}`",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif product.delivery_type == constants.DELIVERY_LICENCA:
            await bot.send_message(
                chat_id=chat_id,
                text=f"📦 Seu produto *{product.name}*.\n\nLicença:\n`{content}`",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif product.delivery_type == constants.DELIVERY_CONVITE:
            await bot.send_message(
                chat_id=chat_id,
                text=f"📦 Seu produto *{product.name}* liberado!\n\n📨 Convite de acesso:\n{content}",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            logger.error("Tipo de entrega desconhecido: %s (produto %s)", product.delivery_type, product.id)
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ Houve um problema ao entregar seu produto. Contate o suporte.",
            )
            return

        await bot.send_message(
            chat_id=chat_id,
            text="✅ Entrega concluída! Obrigado pela compra 💜",
        )

    except Exception:
        logger.exception("Falha ao entregar produto %s para o cliente %s", product.id, chat_id)
        raise
