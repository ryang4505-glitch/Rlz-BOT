"""Handlers administrativos para promoções e divulgação automática em grupos."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services import promotion_service, product_service, broadcast_service, group_service
from utils import keyboards
from utils.decorators import admin_only


@admin_only
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔥 *Promoções*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_promotions_menu())


@admin_only
async def list_promotions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    promotions = promotion_service.list_all()
    if not promotions:
        await query.edit_message_text("🔥 Nenhuma promoção cadastrada ainda.",
                                       reply_markup=keyboards.admin_promotions_menu())
        return
    await query.edit_message_text("🔥 *Promoções cadastradas:*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboards.admin_promotion_list_keyboard(promotions))


async def _render_promotion_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, promotion_id: int) -> None:
    promotion = promotion_service.get_by_id(promotion_id)
    if promotion is None:
        await update.callback_query.edit_message_text("⚠️ Promoção não encontrada.",
                                                        reply_markup=keyboards.admin_promotions_menu())
        return
    product = product_service.get_by_id(promotion.product_id) if promotion.product_id else None
    target_ids = promotion.target_group_id_list()
    groups_label = f"{len(target_ids)} grupo(s) selecionado(s)" if target_ids else "Todos os grupos autorizados"
    text = (
        f"🔥 *{promotion.name}*\n\n"
        f"{promotion.text}\n\n"
        f"📦 Produto vinculado: {product.name if product else '(nenhum)'}\n"
        f"👥 Envio para: {groups_label}\n"
        f"⏱ Intervalo: a cada {promotion.interval_minutes} minutos\n"
        f"📡 Divulgação: {'🟢 Ativa' if promotion.active else '⚪ Pausada'}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.admin_promotion_detail_keyboard(promotion)
    )


@admin_only
async def view_promotion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    promotion_id = int(query.data.split(":")[-1])
    await _render_promotion_detail(update, context, promotion_id)


@admin_only
async def toggle_promotion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    promotion_id = int(query.data.split(":")[-1])
    promotion = promotion_service.get_by_id(promotion_id)
    if promotion is None:
        await query.answer("Promoção não encontrada.")
        return

    scheduler = context.application.bot_data["scheduler"]
    new_active = not promotion.active
    promotion_service.set_active(promotion_id, new_active)

    if new_active:
        broadcast_service.schedule_promotion(scheduler, context.bot, promotion_id, promotion.interval_minutes)
        await query.answer("Divulgação ativada!")
    else:
        broadcast_service.unschedule_promotion(scheduler, promotion_id)
        await query.answer("Divulgação pausada.")

    await _render_promotion_detail(update, context, promotion_id)


@admin_only
async def ask_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    promotion_id = int(query.data.split(":")[-1])
    await query.edit_message_text(
        "⚠️ Tem certeza que deseja excluir esta promoção?",
        reply_markup=keyboards.admin_confirm_delete_keyboard("promotions", promotion_id, f"adm:promotions:view:{promotion_id}"),
    )


@admin_only
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    promotion_id = int(query.data.split(":")[-1])
    scheduler = context.application.bot_data["scheduler"]
    broadcast_service.unschedule_promotion(scheduler, promotion_id)
    promotion_service.delete(promotion_id)
    await query.answer("Promoção excluída.")
    await list_promotions(update, context)


# ---------------------------------------------------------------------------
# Fluxo: criar promoção
# ---------------------------------------------------------------------------
@admin_only
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["flow"] = {"type": "promotion_add", "step": "name", "data": {}}
    await query.edit_message_text("➕ Digite o *nome* interno da promoção:", parse_mode=ParseMode.MARKDOWN)


async def handle_add_text(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    step = flow["step"]
    data = flow["data"]
    text = update.message.text.strip()

    if step == "name":
        if not text:
            await update.message.reply_text("⚠️ O nome não pode ficar vazio.")
            return
        data["name"] = text
        flow["step"] = "text"
        await update.message.reply_text("Digite o *texto* que será divulgado nos grupos:", parse_mode=ParseMode.MARKDOWN)
        return

    if step == "text":
        if not text:
            await update.message.reply_text("⚠️ O texto não pode ficar vazio.")
            return
        data["text"] = text
        flow["step"] = "image"
        await update.message.reply_text(
            "Envie uma *imagem ou vídeo* para a promoção, ou digite '-' para não usar mídia:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if step == "image":
        if text == "-":
            data["image_file_id"] = None
            data["media_type"] = "photo"
            await _ask_promotion_groups(update, context, flow)
            return
        await update.message.reply_text("📸 Envie uma imagem/vídeo ou digite '-' para pular.")
        return


async def handle_add_image(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    message = update.message
    if message.photo:
        flow["data"]["image_file_id"] = message.photo[-1].file_id
        flow["data"]["media_type"] = "photo"
    elif message.video:
        flow["data"]["image_file_id"] = message.video.file_id
        flow["data"]["media_type"] = "video"
    else:
        await update.message.reply_text("⚠️ Envie uma imagem/vídeo válido ou digite '-' para pular.")
        return
    await _ask_promotion_groups(update, context, flow)


async def _ask_promotion_groups(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    flow["step"] = "groups"
    groups = group_service.list_authorized()

    if not groups:
        flow["data"]["selected_groups"] = []
        await _ask_promotion_product(update, context, flow)
        return

    text = (
        "Selecione os grupos que devem receber esta promoção (toque para marcar/desmarcar).\n\n"
        "Se não marcar nenhum, ela será enviada para *todos* os grupos autorizados."
    )
    markup = keyboards.group_multiselect_keyboard(groups, set(), "adm:promotions:addgrp")

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def handle_add_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    flow = context.user_data.get("flow")
    if not flow or flow.get("type") != "promotion_add":
        await query.answer()
        return

    groups = group_service.list_authorized()
    selected = set(flow["data"].get("selected_groups", []))
    action = query.data.split(":")[-1]

    if action == "done":
        await query.answer()
        flow["data"]["selected_groups"] = list(selected)
        await _ask_promotion_product(update, context, flow)
        return

    if action == "all":
        selected = set() if len(selected) == len(groups) else {g.id for g in groups}
    else:
        group_id = int(action)
        if group_id in selected:
            selected.discard(group_id)
        else:
            selected.add(group_id)

    flow["data"]["selected_groups"] = list(selected)
    await query.answer()
    await query.edit_message_reply_markup(
        reply_markup=keyboards.group_multiselect_keyboard(groups, selected, "adm:promotions:addgrp")
    )


async def _ask_promotion_product(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict) -> None:
    flow["step"] = "product"
    products = product_service.list_all(only_active=True)

    rows = [
        [InlineKeyboardButton(p.name, callback_data=f"adm:promotions:addprod:{p.id}")]
        for p in products
    ]
    rows.append([InlineKeyboardButton("Nenhum produto (só divulgação)", callback_data="adm:promotions:addprod:none")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="adm:cancel")])

    text = "Vincule um *produto* a esta promoção (opcional):"
    markup = InlineKeyboardMarkup(rows)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def handle_add_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get("flow")
    if not flow or flow.get("type") != "promotion_add":
        return

    raw = query.data.split(":")[-1]
    flow["data"]["product_id"] = None if raw == "none" else int(raw)
    flow["step"] = "interval"

    await query.edit_message_text(
        "Escolha o *intervalo* de divulgação automática:", parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.interval_select_keyboard("adm:promotions:addint"),
    )


async def handle_add_interval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get("flow")
    if not flow or flow.get("type") != "promotion_add":
        return

    interval_minutes = int(query.data.split(":")[-1])
    data = flow["data"]

    selected_groups = data.get("selected_groups") or []
    target_group_ids = ",".join(str(gid) for gid in selected_groups) if selected_groups else None

    promotion = promotion_service.create(
        name=data["name"], text=data["text"], image_file_id=data.get("image_file_id"),
        product_id=data.get("product_id"), interval_minutes=interval_minutes,
        media_type=data.get("media_type", "photo"),
        target_group_ids=target_group_ids,
    )
    context.user_data.pop("flow", None)

    await query.edit_message_text(
        f"✅ Promoção *{promotion.name}* criada!\n\n"
        "Ative a divulgação na tela de detalhes da promoção quando quiser começar a enviar.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.admin_promotions_menu(),
    )
