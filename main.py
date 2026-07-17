"""
main.py
--------
Ponto de entrada do bot de loja digital para Telegram.

Responsável por:
  - Validar configurações e inicializar o banco de dados.
  - Registrar todos os handlers (cliente, admin, eventos de grupo).
  - Iniciar o APScheduler para a divulgação automática de promoções.
  - Rodar o bot em modo polling.
"""

import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database
from utils.logger import setup_logger
from services import broadcast_service

from handlers.client import start, catalog, purchase, orders as client_orders, support, promotions as client_promotions
from handlers.admin import (
    panel,
    products as admin_products,
    categories as admin_categories,
    promotions as admin_promotions,
    groups as admin_groups,
    pix as admin_pix,
    orders as admin_orders,
    customers as admin_customers,
    stats as admin_stats,
)
from handlers import group_events, input_router

logger = logging.getLogger("shop_bot.main")


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erro não tratado durante o processamento de um update: %s", context.error, exc_info=context.error)


async def _post_init(application: Application) -> None:
    """Executado uma vez após a inicialização da Application (antes do polling)."""
    scheduler: AsyncIOScheduler = application.bot_data["scheduler"]
    scheduler.start()
    broadcast_service.load_and_schedule_active_promotions(scheduler, application.bot)
    logger.info("Bot iniciado e pronto. Scheduler ativo com %s job(s).", len(scheduler.get_jobs()))


def _register_handlers(application: Application) -> None:
    # ------------------------------------------------------------------
    # Cliente
    # ------------------------------------------------------------------
    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CallbackQueryHandler(start.show_main_menu, pattern=r"^menu:main$"))

    application.add_handler(CallbackQueryHandler(catalog.list_categories, pattern=r"^cat:list$"))
    application.add_handler(CallbackQueryHandler(catalog.show_category_products, pattern=r"^cat:\d+$"))
    application.add_handler(CallbackQueryHandler(catalog.show_product_detail, pattern=r"^prod:\d+$"))

    application.add_handler(CallbackQueryHandler(client_promotions.list_promotions, pattern=r"^promo:list$"))

    application.add_handler(CallbackQueryHandler(purchase.start_purchase_callback, pattern=r"^buy:"))

    application.add_handler(CallbackQueryHandler(client_orders.list_my_orders, pattern=r"^orders:list$"))
    application.add_handler(CallbackQueryHandler(client_orders.show_order_detail, pattern=r"^order:\d+$"))

    application.add_handler(CallbackQueryHandler(support.start_support, pattern=r"^support:start$"))

    # ------------------------------------------------------------------
    # Painel administrativo
    # ------------------------------------------------------------------
    application.add_handler(CommandHandler("admin", panel.cmd_panel))
    application.add_handler(CommandHandler("painel", panel.cmd_panel))
    application.add_handler(CallbackQueryHandler(panel.show_menu, pattern=r"^adm:menu$"))
    application.add_handler(CallbackQueryHandler(panel.cancel_flow, pattern=r"^adm:cancel$"))

    # Produtos
    application.add_handler(CallbackQueryHandler(admin_products.menu, pattern=r"^adm:products$"))
    application.add_handler(CallbackQueryHandler(admin_products.start_add, pattern=r"^adm:products:add$"))
    application.add_handler(CallbackQueryHandler(admin_products.list_products, pattern=r"^adm:products:list$"))
    application.add_handler(CallbackQueryHandler(admin_products.view_product, pattern=r"^adm:products:view:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.toggle_product, pattern=r"^adm:products:toggle:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.ask_delete, pattern=r"^adm:products:delete:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.confirm_delete, pattern=r"^adm:products:delconfirm:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.edit_menu, pattern=r"^adm:products:editmenu:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.start_edit_field, pattern=r"^adm:products:editfield:\d+:\w+$"))
    application.add_handler(CallbackQueryHandler(admin_products.handle_add_category_callback, pattern=r"^adm:products:addcat:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.handle_add_delivery_type_callback, pattern=r"^adm:products:adddel:\w+$"))
    application.add_handler(CallbackQueryHandler(admin_products.handle_edit_category_callback, pattern=r"^adm:products:editcat:\d+:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_products.handle_edit_delivery_type_callback, pattern=r"^adm:products:editdeltype:\d+:\w+$"))

    # Categorias
    application.add_handler(CallbackQueryHandler(admin_categories.menu, pattern=r"^adm:categories$"))
    application.add_handler(CallbackQueryHandler(admin_categories.start_add, pattern=r"^adm:categories:add$"))
    application.add_handler(CallbackQueryHandler(admin_categories.list_categories, pattern=r"^adm:categories:list$"))
    application.add_handler(CallbackQueryHandler(admin_categories.view_category, pattern=r"^adm:categories:view:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_categories.toggle_category, pattern=r"^adm:categories:toggle:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_categories.ask_delete, pattern=r"^adm:categories:delete:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_categories.confirm_delete, pattern=r"^adm:categories:delconfirm:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_categories.start_edit_name, pattern=r"^adm:categories:editname:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_categories.start_edit_description, pattern=r"^adm:categories:editdesc:\d+$"))

    # Promoções
    application.add_handler(CallbackQueryHandler(admin_promotions.menu, pattern=r"^adm:promotions$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.start_add, pattern=r"^adm:promotions:add$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.list_promotions, pattern=r"^adm:promotions:list$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.view_promotion, pattern=r"^adm:promotions:view:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.toggle_promotion, pattern=r"^adm:promotions:toggle:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.ask_delete, pattern=r"^adm:promotions:delete:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.confirm_delete, pattern=r"^adm:promotions:delconfirm:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.handle_add_group_callback, pattern=r"^adm:promotions:addgrp:(\d+|all|done)$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.handle_add_product_callback, pattern=r"^adm:promotions:addprod:(\d+|none)$"))
    application.add_handler(CallbackQueryHandler(admin_promotions.handle_add_interval_callback, pattern=r"^adm:promotions:addint:\d+$"))

    # Grupos
    application.add_handler(CallbackQueryHandler(admin_groups.menu, pattern=r"^adm:groups$"))
    application.add_handler(CallbackQueryHandler(admin_groups.view_group, pattern=r"^adm:groups:view:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_groups.authorize_group, pattern=r"^adm:groups:authorize:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_groups.block_group, pattern=r"^adm:groups:block:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_groups.remove_group, pattern=r"^adm:groups:remove:\d+$"))

    # Pix
    application.add_handler(CallbackQueryHandler(admin_pix.menu, pattern=r"^adm:pix$"))
    application.add_handler(CallbackQueryHandler(admin_pix.start_edit, pattern=r"^adm:pix:edit$"))

    # Pedidos / pagamentos
    application.add_handler(CallbackQueryHandler(admin_orders.menu, pattern=r"^adm:orders$"))
    application.add_handler(CallbackQueryHandler(admin_orders.view_order, pattern=r"^adm:orders:view:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_orders.approve_payment, pattern=r"^adm:pay:approve:\d+$"))
    application.add_handler(CallbackQueryHandler(admin_orders.reject_payment, pattern=r"^adm:pay:reject:\d+$"))

    # Clientes e estatísticas
    application.add_handler(CallbackQueryHandler(admin_customers.menu, pattern=r"^adm:customers$"))
    application.add_handler(CallbackQueryHandler(admin_stats.menu, pattern=r"^adm:stats$"))

    # ------------------------------------------------------------------
    # Eventos de grupo (detecção automática)
    # ------------------------------------------------------------------
    application.add_handler(ChatMemberHandler(group_events.on_bot_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))

    # ------------------------------------------------------------------
    # Entradas livres (texto / mídia) roteadas por fluxo com estado
    # ------------------------------------------------------------------
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_router.route_text))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, input_router.route_media))

    application.add_error_handler(_on_error)


def main() -> None:
    config.validate_config()
    setup_logger()
    logger.info("Inicializando banco de dados...")
    database.init_db()

    application = ApplicationBuilder().token(config.BOT_TOKEN).post_init(_post_init).build()

    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    application.bot_data["scheduler"] = scheduler

    _register_handlers(application)

    logger.info("Iniciando bot em modo polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
