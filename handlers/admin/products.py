"""Handlers administrativos para cadastro, edição e remoção de produtos."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import product_service, category_service
from utils import keyboards, constants
from utils.decorators import admin_only

logger = logging.getLogger("shop_bot.admin.products")


# ---------------------------------------------------------------------------
# Menus e listagem
# ---------------------------------------------------------------------------
@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📦 *Produtos*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_products_menu())


@admin_only
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    products = product_service.list_all()
    if not products:
        await query.edit_message_text("📦 Nenhum produto cadastrado ainda.",
                                       reply_markup=keyboards.admin_products_menu())
        return
    await query.edit_message_text("📦 *Produtos cadastrados:*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_product_list_keyboard(products))


@admin_only
async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":")[-1])
    await _render_product_detail(update, context, product_id)


async def _render_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int) -> None:
    product = product_service.get_by_id(product_id)
    if product is None:
        await update.callback_query.edit_message_text(
            "⚠️ Produto não encontrado.", reply_markup=keyboards.admin_products_menu()
        )
        return

    category = category_service.get_by_id(product.category_id)
    photos = product_service.list_photos(product.id)

    text = (
        f"📦 *{product.name}*\n\n"
        f"{product.description or '(sem descrição)'}\n\n"
        f"🗂 Categoria: {category.name if category else '(removida)'}\n"
        f"💰 Preço: R$ {product.price:.2f}\n"
        f"🚚 Entrega: {constants.DELIVERY_TYPE_LABELS.get(product.delivery_type, product.delivery_type)}\n"
        f"🖼 Fotos: {len(photos)}\n"
        f"Status: {'🟢 Ativo' if product.active else '🔴 Inativo'}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_product_detail_keyboard(product)
    )


@admin_only
async def toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    product_id = int(query.data.split(":")[-1])
    product_service.toggle_active(product_id)
    await query.answer("Status atualizado.")
    await _render_product_detail(update, context, product_id)


@admin_only
async def ask_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":")[-1])
    await query.edit_message_text(
        "⚠️ Tem certeza que deseja excluir este produto? Essa ação não pode ser desfeita.",
        reply_markup=keyboards.admin_confirm_delete_keyboard("products", product_id, f"adm:products:view:{product_id}"),
    )


@admin_only
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    product_id = int(query.data.split(":")[-1])
    deleted = product_service.delete(product_id)
    if deleted:
        await query.answer("Produto excluído.")
    else:
        await query.answer("Produto já tem pedidos — foi desativado em vez de excluído.", show_alert=True)
    await list_products(update, context)


# ---------------------------------------------------------------------------
# Fluxo: adicionar produto
# ---------------------------------------------------------------------------
@admin_only
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    context.user_data["flow"] = {"type": "product_add", "step": "name", "data": {}}
    await query.edit_message_text(
        "➕ *Novo produto*\n\nDigite o *nome* do produto:", parse_mode=ParseMode.MARKDOWN
    )


async def handle_add_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    step = flow["step"]
    data = flow["data"]
    text = update.message.text.strip()

    if step == "name":
        if not text:
            await update.message.reply_text("⚠️ O nome não pode ficar vazio. Digite novamente:")
            return
        data["name"] = text
        flow["step"] = "description"
        await update.message.reply_text("Digite a *descrição* do produto (envie '-' para deixar vazio):",
                                         parse_mode=ParseMode.MARKDOWN)
        return

    if step == "description":
        data["description"] = None if text == "-" else text
        categories = category_service.list_all(only_active=True)
        if not categories:
            context.user_data.pop("flow", None)
            await update.message.reply_text(
                "⚠️ Nenhuma categoria cadastrada. Crie uma categoria antes de adicionar produtos.",
                reply_markup=keyboards.admin_products_menu(),
            )
            return
        flow["step"] = "category"
        await update.message.reply_text(
            "Escolha a *categoria* do produto:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboards.category_select_keyboard(categories, "adm:products:addcat"),
        )
        return

    if step == "price":
        normalized = text.replace(",", ".")
        try:
            price = float(normalized)
            if price <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Preço inválido. Digite um valor numérico, ex: 29.90")
            return
        data["price"] = round(price, 2)
        flow["step"] = "delivery_type"
        await update.message.reply_text(
            "Escolha o *método de entrega* do produto:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboards.delivery_type_keyboard("adm:products:adddel"),
        )
        return

    if step == "delivery_content":
        data["delivery_content"] = text
        flow["step"] = "photos"
        data.setdefault("photos", [])
        await update.message.reply_text(
            "Envie as *fotos ou vídeos* do produto (um ou mais). Quando terminar, digite *concluir*.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if step == "photos":
        if text.lower() in ("concluir", "pronto", "finalizar"):
            await _finalize_add_product(update, context, flow)
            return
        await update.message.reply_text(
            "📸 Envie uma foto/vídeo ou digite *concluir* para finalizar o cadastro.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return


async def handle_add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get("flow")
    if not flow or flow.get("type") != "product_add":
        return

    category_id = int(query.data.split(":")[-1])
    flow["data"]["category_id"] = category_id
    flow["step"] = "price"
    await query.edit_message_text("Digite o *preço* do produto (ex: 29.90):", parse_mode=ParseMode.MARKDOWN)


async def handle_add_delivery_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get("flow")
    if not flow or flow.get("type") != "product_add":
        return

    delivery_type = query.data.split(":")[-1]
    flow["data"]["delivery_type"] = delivery_type

    if delivery_type == constants.DELIVERY_ARQUIVO:
        flow["step"] = "delivery_file"
        await query.edit_message_text("📁 Envie o *arquivo* que será entregue ao cliente.",
                                       parse_mode=ParseMode.MARKDOWN)
    else:
        flow["step"] = "delivery_content"
        prompt = {
            constants.DELIVERY_LINK: "Digite o *link* que será enviado ao cliente:",
            constants.DELIVERY_TEXTO: "Digite o *texto* que será enviado ao cliente:",
            constants.DELIVERY_CODIGO: "Digite o *código* que será enviado ao cliente:",
            constants.DELIVERY_LICENCA: "Digite a *licença* que será enviada ao cliente:",
            constants.DELIVERY_CONVITE: "Digite o *link de convite* do grupo/canal:",
        }[delivery_type]
        await query.edit_message_text(prompt, parse_mode=ParseMode.MARKDOWN)


async def handle_add_delivery_file(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    document = update.message.document
    if not document:
        await update.message.reply_text("⚠️ Envie o conteúdo como *arquivo*.", parse_mode=ParseMode.MARKDOWN)
        return
    flow["data"]["delivery_content"] = document.file_id
    flow["step"] = "photos"
    flow["data"].setdefault("photos", [])
    await update.message.reply_text(
        "Envie as *fotos ou vídeos* do produto (um ou mais). Quando terminar, digite *concluir*.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    message = update.message
    if message.photo:
        flow["data"].setdefault("photos", []).append({"file_id": message.photo[-1].file_id, "media_type": "photo"})
    elif message.video:
        flow["data"].setdefault("photos", []).append({"file_id": message.video.file_id, "media_type": "video"})
    else:
        await update.message.reply_text("⚠️ Envie uma foto ou vídeo válido, ou digite *concluir*.",
                                         parse_mode=ParseMode.MARKDOWN)
        return
    total = len(flow["data"]["photos"])
    await update.message.reply_text(f"📸 Mídia {total} adicionada. Envie mais ou digite *concluir*.",
                                     parse_mode=ParseMode.MARKDOWN)


async def _finalize_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    data = flow["data"]
    product = product_service.create(
        category_id=data["category_id"],
        name=data["name"],
        description=data.get("description"),
        price=data["price"],
        delivery_type=data["delivery_type"],
        delivery_content=data.get("delivery_content"),
    )
    for item in data.get("photos", []):
        product_service.add_photo(product.id, item["file_id"], item["media_type"])

    context.user_data.pop("flow", None)
    await update.message.reply_text(
        f"✅ Produto *{product.name}* cadastrado com sucesso!", parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.admin_products_menu(),
    )


# ---------------------------------------------------------------------------
# Fluxo: editar produto
# ---------------------------------------------------------------------------
@admin_only
async def edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":")[-1])
    await query.edit_message_text(
        "✏️ Escolha o campo que deseja editar:",
        reply_markup=keyboards.admin_product_edit_fields_keyboard(product_id),
    )


@admin_only
async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, _, product_id_raw, field = query.data.split(":")
    product_id = int(product_id_raw)

    if field == "category":
        categories = category_service.list_all(only_active=True)
        await query.edit_message_text(
            "Escolha a nova categoria:",
            reply_markup=keyboards.category_select_keyboard(categories, f"adm:products:editcat:{product_id}"),
        )
        return

    if field == "delivery":
        await query.edit_message_text(
            "Escolha o novo método de entrega:",
            reply_markup=keyboards.delivery_type_keyboard(f"adm:products:editdeltype:{product_id}"),
        )
        return

    if field == "photos":
        context.user_data["flow"] = {"type": "product_edit_photos", "product_id": product_id, "data": {"photos": []}}
        await query.edit_message_text(
            "As fotos/vídeos atuais serão substituídos. Envie as novas *fotos ou vídeos* e depois digite *concluir*.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    field_prompts = {
        "name": "Digite o novo *nome*:",
        "description": "Digite a nova *descrição*:",
        "price": "Digite o novo *preço* (ex: 29.90):",
    }
    context.user_data["flow"] = {"type": "product_edit_field", "product_id": product_id, "field": field}
    await query.edit_message_text(field_prompts[field], parse_mode=ParseMode.MARKDOWN)


async def handle_edit_field_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    product_id = flow["product_id"]
    field = flow["field"]
    text = update.message.text.strip()

    if field == "price":
        normalized = text.replace(",", ".")
        try:
            value = round(float(normalized), 2)
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Preço inválido. Digite um valor numérico, ex: 29.90")
            return
    elif field == "description":
        value = None if text == "-" else text
    else:
        if not text:
            await update.message.reply_text("⚠️ Valor não pode ficar vazio.")
            return
        value = text

    product_service.update_field(product_id, field, value)
    context.user_data.pop("flow", None)
    await update.message.reply_text("✅ Produto atualizado!", reply_markup=keyboards.admin_products_menu())


async def handle_edit_photos(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    message = update.message
    if message.photo:
        flow["data"]["photos"].append({"file_id": message.photo[-1].file_id, "media_type": "photo"})
        total = len(flow["data"]["photos"])
        await message.reply_text(f"📸 Mídia {total} adicionada. Envie mais ou digite *concluir*.",
                                  parse_mode=ParseMode.MARKDOWN)
        return

    if message.video:
        flow["data"]["photos"].append({"file_id": message.video.file_id, "media_type": "video"})
        total = len(flow["data"]["photos"])
        await message.reply_text(f"📸 Mídia {total} adicionada. Envie mais ou digite *concluir*.",
                                  parse_mode=ParseMode.MARKDOWN)
        return

    if message.text and message.text.strip().lower() in ("concluir", "pronto", "finalizar"):
        product_id = flow["product_id"]
        product_service.clear_photos(product_id)
        for item in flow["data"]["photos"]:
            product_service.add_photo(product_id, item["file_id"], item["media_type"])
        context.user_data.pop("flow", None)
        await message.reply_text("✅ Fotos/vídeos atualizados!", reply_markup=keyboards.admin_products_menu())
        return

    await message.reply_text("📸 Envie uma foto/vídeo ou digite *concluir* para finalizar.", parse_mode=ParseMode.MARKDOWN)


async def handle_edit_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    product_id, category_id = int(parts[-2]), int(parts[-1])
    product_service.update_field(product_id, "category_id", category_id)
    context.user_data.pop("flow", None)
    await query.edit_message_text("✅ Categoria atualizada!", reply_markup=keyboards.admin_products_menu())


async def handle_edit_delivery_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    product_id, delivery_type = int(parts[-2]), parts[-1]

    if delivery_type == constants.DELIVERY_ARQUIVO:
        context.user_data["flow"] = {
            "type": "product_edit_delivery_file", "product_id": product_id, "delivery_type": delivery_type,
        }
        await query.edit_message_text("📁 Envie o novo *arquivo* de entrega.", parse_mode=ParseMode.MARKDOWN)
        return

    context.user_data["flow"] = {
        "type": "product_edit_delivery_content", "product_id": product_id, "delivery_type": delivery_type,
    }
    prompt = {
        constants.DELIVERY_LINK: "Digite o novo *link*:",
        constants.DELIVERY_TEXTO: "Digite o novo *texto*:",
        constants.DELIVERY_CODIGO: "Digite o novo *código*:",
        constants.DELIVERY_LICENCA: "Digite a nova *licença*:",
        constants.DELIVERY_CONVITE: "Digite o novo *link de convite*:",
    }[delivery_type]
    await query.edit_message_text(prompt, parse_mode=ParseMode.MARKDOWN)


async def handle_edit_delivery_file(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    document = update.message.document
    if not document:
        await update.message.reply_text("⚠️ Envie o conteúdo como *arquivo*.", parse_mode=ParseMode.MARKDOWN)
        return
    product_id = flow["product_id"]
    product_service.update_field(product_id, "delivery_type", flow["delivery_type"])
    product_service.update_field(product_id, "delivery_content", document.file_id)
    context.user_data.pop("flow", None)
    await update.message.reply_text("✅ Entrega atualizada!", reply_markup=keyboards.admin_products_menu())


async def handle_edit_delivery_content_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ O conteúdo não pode ficar vazio.")
        return
    product_id = flow["product_id"]
    product_service.update_field(product_id, "delivery_type", flow["delivery_type"])
    product_service.update_field(product_id, "delivery_content", text)
    context.user_data.pop("flow", None)
    await update.message.reply_text("✅ Entrega atualizada!", reply_markup=keyboards.admin_products_menu())
