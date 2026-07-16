"""Construtores de InlineKeyboardMarkup reutilizados pelos handlers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton

from models.category import Category
from models.product import Product
from models.promotion import Promotion
from models.group import Group
from models.order import Order
from utils import constants


# ---------------------------------------------------------------------------
# Menus do cliente
# ---------------------------------------------------------------------------
def client_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Produtos", callback_data="cat:list")],
        [InlineKeyboardButton("🔥 Promoções", callback_data="promo:list")],
        [InlineKeyboardButton("📦 Meus pedidos", callback_data="orders:list")],
        [InlineKeyboardButton("💬 Suporte", callback_data="support:start")],
    ])


def back_to_menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu inicial", callback_data="menu:main")]])


def categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(c.name, callback_data=f"cat:{c.id}")] for c in categories]
    rows.append([InlineKeyboardButton("⬅️ Menu inicial", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(products: list[Product], category_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{p.name} — R$ {p.price:.2f}", callback_data=f"prod:{p.id}")]
        for p in products
    ]
    rows.append([InlineKeyboardButton("⬅️ Categorias", callback_data="cat:list")])
    return InlineKeyboardMarkup(rows)


def product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar Agora", callback_data=f"buy:{product_id}")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data=f"cat:{category_id}")],
    ])


def orders_keyboard(orders: list[Order]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"#{o.id} · {constants.ORDER_STATUS_LABELS.get(o.status, o.status)}",
            callback_data=f"order:{o.id}",
        )]
        for o in orders
    ]
    rows.append([InlineKeyboardButton("⬅️ Menu inicial", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def send_proof_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar compra", callback_data="buy:cancel")]])


def pix_payment_keyboard(pix_key: str) -> InlineKeyboardMarkup:
    """Teclado com botão nativo de 'copiar para a área de transferência' da chave Pix."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copiar chave Pix", copy_text=CopyTextButton(text=pix_key))],
        [InlineKeyboardButton("❌ Cancelar compra", callback_data="buy:cancel")],
    ])


# ---------------------------------------------------------------------------
# Painel administrativo
# ---------------------------------------------------------------------------
def admin_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Produtos", callback_data="adm:products"),
         InlineKeyboardButton("🗂 Categorias", callback_data="adm:categories")],
        [InlineKeyboardButton("🔥 Promoções", callback_data="adm:promotions"),
         InlineKeyboardButton("👥 Grupos", callback_data="adm:groups")],
        [InlineKeyboardButton("💠 Pix", callback_data="adm:pix"),
         InlineKeyboardButton("🧾 Pedidos", callback_data="adm:orders")],
        [InlineKeyboardButton("🙋 Clientes", callback_data="adm:customers"),
         InlineKeyboardButton("📊 Estatísticas", callback_data="adm:stats")],
    ])


def admin_back_button(target: str = "adm:menu") -> InlineKeyboardButton:
    return InlineKeyboardButton("⬅️ Voltar", callback_data=target)


def admin_products_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Adicionar produto", callback_data="adm:products:add")],
        [InlineKeyboardButton("📋 Listar produtos", callback_data="adm:products:list")],
        [admin_back_button()],
    ])


def admin_product_list_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{'🟢' if p.active else '🔴'} {p.name}", callback_data=f"adm:products:view:{p.id}")]
        for p in products
    ]
    rows.append([admin_back_button("adm:products")])
    return InlineKeyboardMarkup(rows)


def admin_product_detail_keyboard(product: Product) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Desativar" if product.active else "🟢 Ativar"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Editar", callback_data=f"adm:products:editmenu:{product.id}")],
        [InlineKeyboardButton(toggle_label, callback_data=f"adm:products:toggle:{product.id}")],
        [InlineKeyboardButton("🗑 Excluir", callback_data=f"adm:products:delete:{product.id}")],
        [admin_back_button("adm:products:list")],
    ])


def admin_product_edit_fields_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Nome", callback_data=f"adm:products:editfield:{product_id}:name")],
        [InlineKeyboardButton("Descrição", callback_data=f"adm:products:editfield:{product_id}:description")],
        [InlineKeyboardButton("Preço", callback_data=f"adm:products:editfield:{product_id}:price")],
        [InlineKeyboardButton("Categoria", callback_data=f"adm:products:editfield:{product_id}:category")],
        [InlineKeyboardButton("Entrega", callback_data=f"adm:products:editfield:{product_id}:delivery")],
        [InlineKeyboardButton("Fotos", callback_data=f"adm:products:editfield:{product_id}:photos")],
        [admin_back_button(f"adm:products:view:{product_id}")],
    ])


def admin_confirm_delete_keyboard(entity: str, entity_id: int, back_target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirmar exclusão", callback_data=f"adm:{entity}:delconfirm:{entity_id}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data=back_target)],
    ])


def admin_categories_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Adicionar categoria", callback_data="adm:categories:add")],
        [InlineKeyboardButton("📋 Listar categorias", callback_data="adm:categories:list")],
        [admin_back_button()],
    ])


def admin_category_list_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{'🟢' if c.active else '🔴'} {c.name}", callback_data=f"adm:categories:view:{c.id}")]
        for c in categories
    ]
    rows.append([admin_back_button("adm:categories")])
    return InlineKeyboardMarkup(rows)


def admin_category_detail_keyboard(category: Category) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Desativar" if category.active else "🟢 Ativar"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Editar nome", callback_data=f"adm:categories:editname:{category.id}")],
        [InlineKeyboardButton("✏️ Editar descrição", callback_data=f"adm:categories:editdesc:{category.id}")],
        [InlineKeyboardButton(toggle_label, callback_data=f"adm:categories:toggle:{category.id}")],
        [InlineKeyboardButton("🗑 Excluir", callback_data=f"adm:categories:delete:{category.id}")],
        [admin_back_button("adm:categories:list")],
    ])


def category_select_keyboard(categories: list[Category], callback_prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(c.name, callback_data=f"{callback_prefix}:{c.id}")] for c in categories]
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(rows)


def delivery_type_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"{callback_prefix}:{key}")]
        for key, label in constants.DELIVERY_TYPE_LABELS.items()
    ]
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(rows)


def admin_promotions_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Criar promoção", callback_data="adm:promotions:add")],
        [InlineKeyboardButton("📋 Listar promoções", callback_data="adm:promotions:list")],
        [admin_back_button()],
    ])


def admin_promotion_list_keyboard(promotions: list[Promotion]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{'🟢' if p.active else '⚪'} {p.name}", callback_data=f"adm:promotions:view:{p.id}")]
        for p in promotions
    ]
    rows.append([admin_back_button("adm:promotions")])
    return InlineKeyboardMarkup(rows)


def admin_promotion_detail_keyboard(promotion: Promotion) -> InlineKeyboardMarkup:
    toggle_label = "⏸ Desativar divulgação" if promotion.active else "▶️ Ativar divulgação"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=f"adm:promotions:toggle:{promotion.id}")],
        [InlineKeyboardButton("🗑 Excluir", callback_data=f"adm:promotions:delete:{promotion.id}")],
        [admin_back_button("adm:promotions:list")],
    ])


def interval_select_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{m} minutos", callback_data=f"{callback_prefix}:{m}")]
        for m in constants.BROADCAST_INTERVALS
    ]
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(rows)


def group_multiselect_keyboard(groups: list[Group], selected_ids: set[int], callback_prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for g in groups:
        mark = "✅" if g.id in selected_ids else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {g.title or g.chat_id}", callback_data=f"{callback_prefix}:{g.id}")])
    rows.append([InlineKeyboardButton("☑️ Marcar/Desmarcar todos", callback_data=f"{callback_prefix}:all")])
    rows.append([InlineKeyboardButton("➡️ Concluir seleção", callback_data=f"{callback_prefix}:done")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(rows)


def admin_groups_menu(groups: list[Group]) -> InlineKeyboardMarkup:
    rows = []
    for g in groups:
        label = f"{constants.GROUP_STATUS_LABELS.get(g.status, g.status)} · {g.title or g.chat_id}"
        rows.append([InlineKeyboardButton(label, callback_data=f"adm:groups:view:{g.id}")])
    rows.append([admin_back_button()])
    return InlineKeyboardMarkup(rows)


def admin_group_detail_keyboard(group: Group) -> InlineKeyboardMarkup:
    rows = []
    if group.status != constants.GROUP_AUTHORIZED:
        rows.append([InlineKeyboardButton("✅ Autorizar", callback_data=f"adm:groups:authorize:{group.id}")])
    if group.status != constants.GROUP_BLOCKED:
        rows.append([InlineKeyboardButton("🚫 Bloquear", callback_data=f"adm:groups:block:{group.id}")])
    rows.append([InlineKeyboardButton("🗑 Remover", callback_data=f"adm:groups:remove:{group.id}")])
    rows.append([admin_back_button("adm:groups")])
    return InlineKeyboardMarkup(rows)


def admin_order_detail_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Aprovar pagamento", callback_data=f"adm:pay:approve:{order_id}")],
        [InlineKeyboardButton("❌ Recusar pagamento", callback_data=f"adm:pay:reject:{order_id}")],
    ])


def admin_orders_list_keyboard(orders: list[Order]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"#{o.id} · {constants.ORDER_STATUS_LABELS.get(o.status, o.status)}",
            callback_data=f"adm:orders:view:{o.id}",
        )]
        for o in orders
    ]
    rows.append([admin_back_button()])
    return InlineKeyboardMarkup(rows)


def yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim", callback_data=yes_callback),
         InlineKeyboardButton("❌ Não", callback_data=no_callback)],
    ])
