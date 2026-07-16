"""Handler administrativo para exibição de estatísticas gerais da loja."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import stats_service
from utils import keyboards
from utils.decorators import admin_only


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    stats = stats_service.build_stats()
    text = (
        "📊 *Estatísticas da loja*\n\n"
        f"🙋 Clientes cadastrados: {stats.total_customers}\n"
        f"📦 Produtos cadastrados: {stats.total_products}\n"
        f"🧾 Pedidos totais: {stats.total_orders}\n"
        f"🔎 Pedidos aguardando análise: {stats.orders_pending_review}\n"
        f"👥 Grupos detectados: {stats.total_groups}\n"
        f"✅ Grupos autorizados: {stats.authorized_groups}\n"
        f"💰 Receita aprovada: R$ {stats.approved_revenue:.2f}"
    )

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_back_button())
