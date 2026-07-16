"""Handlers administrativos para cadastro, edição e remoção de categorias."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import category_service
from utils import keyboards
from utils.decorators import admin_only


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🗂 *Categorias*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_categories_menu())


@admin_only
async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    categories = category_service.list_all()
    if not categories:
        await query.edit_message_text("🗂 Nenhuma categoria cadastrada ainda.",
                                       reply_markup=keyboards.admin_categories_menu())
        return
    await query.edit_message_text("🗂 *Categorias cadastradas:*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_category_list_keyboard(categories))


async def _render_category_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int) -> None:
    category = category_service.get_by_id(category_id)
    if category is None:
        await update.callback_query.edit_message_text("⚠️ Categoria não encontrada.",
                                                        reply_markup=keyboards.admin_categories_menu())
        return
    text = (
        f"🗂 *{category.name}*\n\n"
        f"{category.description or '(sem descrição)'}\n\n"
        f"Status: {'🟢 Ativa' if category.active else '🔴 Inativa'}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_category_detail_keyboard(category)
    )


@admin_only
async def view_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":")[-1])
    await _render_category_detail(update, context, category_id)


@admin_only
async def toggle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    category_id = int(query.data.split(":")[-1])
    category_service.toggle_active(category_id)
    await query.answer("Status atualizado.")
    await _render_category_detail(update, context, category_id)


@admin_only
async def ask_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    category_id = int(query.data.split(":")[-1])
    if category_service.has_products(category_id):
        await query.answer()
        await query.edit_message_text(
            "⚠️ Existem produtos nesta categoria. Remova ou mova os produtos antes de excluí-la.",
            reply_markup=keyboards.admin_back_button(f"adm:categories:view:{category_id}"),
        )
        return
    await query.answer()
    await query.edit_message_text(
        "⚠️ Tem certeza que deseja excluir esta categoria?",
        reply_markup=keyboards.admin_confirm_delete_keyboard("categories", category_id, f"adm:categories:view:{category_id}"),
    )


@admin_only
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    category_id = int(query.data.split(":")[-1])
    category_service.delete(category_id)
    await query.answer("Categoria excluída.")
    await list_categories(update, context)


# ---------------------------------------------------------------------------
# Fluxo: adicionar categoria
# ---------------------------------------------------------------------------
@admin_only
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["flow"] = {"type": "category_add", "step": "name", "data": {}}
    await query.edit_message_text("➕ Digite o *nome* da nova categoria:", parse_mode=ParseMode.MARKDOWN)


async def handle_add_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    step = flow["step"]
    data = flow["data"]
    text = update.message.text.strip()

    if step == "name":
        if not text:
            await update.message.reply_text("⚠️ O nome não pode ficar vazio.")
            return
        data["name"] = text
        flow["step"] = "description"
        await update.message.reply_text("Digite a *descrição* da categoria (envie '-' para deixar vazio):",
                                         parse_mode=ParseMode.MARKDOWN)
        return

    if step == "description":
        description = None if text == "-" else text
        category = category_service.create(name=data["name"], description=description)
        context.user_data.pop("flow", None)
        await update.message.reply_text(
            f"✅ Categoria *{category.name}* criada com sucesso!", parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboards.admin_categories_menu(),
        )
        return


# ---------------------------------------------------------------------------
# Fluxo: editar categoria
# ---------------------------------------------------------------------------
@admin_only
async def start_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":")[-1])
    context.user_data["flow"] = {"type": "category_edit_name", "category_id": category_id}
    await query.edit_message_text("Digite o novo *nome* da categoria:", parse_mode=ParseMode.MARKDOWN)


@admin_only
async def start_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":")[-1])
    context.user_data["flow"] = {"type": "category_edit_desc", "category_id": category_id}
    await query.edit_message_text("Digite a nova *descrição* da categoria:", parse_mode=ParseMode.MARKDOWN)


async def handle_edit_name_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ O nome não pode ficar vazio.")
        return
    category_service.update_name(flow["category_id"], text)
    context.user_data.pop("flow", None)
    await update.message.reply_text("✅ Nome atualizado!", reply_markup=keyboards.admin_categories_menu())


async def handle_edit_desc_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    text = update.message.text.strip()
    category_service.update_description(flow["category_id"], text)
    context.user_data.pop("flow", None)
    await update.message.reply_text("✅ Descrição atualizada!", reply_markup=keyboards.admin_categories_menu())
