"""Regras de negócio (CRUD) para produtos digitais e suas fotos."""

from typing import Optional

import database
from models.product import Product, ProductPhoto


def create(category_id: int, name: str, description: Optional[str], price: float,
           delivery_type: str, delivery_content: Optional[str]) -> Product:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO products
               (category_id, name, description, price, delivery_type, delivery_content)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (category_id, name, description, price, delivery_type, delivery_content),
        )
        cur.execute("SELECT * FROM products WHERE id = ?", (cur.lastrowid,))
        return Product.from_row(cur.fetchone())


def get_by_id(product_id: int) -> Optional[Product]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cur.fetchone()
        return Product.from_row(row) if row else None


def list_by_category(category_id: int, only_active: bool = True) -> list[Product]:
    with database.get_cursor() as cur:
        if only_active:
            cur.execute(
                "SELECT * FROM products WHERE category_id = ? AND active = 1 ORDER BY name",
                (category_id,),
            )
        else:
            cur.execute("SELECT * FROM products WHERE category_id = ? ORDER BY name", (category_id,))
        return [Product.from_row(r) for r in cur.fetchall()]


def list_all(only_active: bool = False) -> list[Product]:
    with database.get_cursor() as cur:
        if only_active:
            cur.execute("SELECT * FROM products WHERE active = 1 ORDER BY name")
        else:
            cur.execute("SELECT * FROM products ORDER BY name")
        return [Product.from_row(r) for r in cur.fetchall()]


def update_field(product_id: int, field: str, value) -> None:
    allowed_fields = {"name", "description", "price", "category_id", "delivery_type", "delivery_content"}
    if field not in allowed_fields:
        raise ValueError(f"Campo não permitido para atualização: {field}")
    with database.get_cursor(commit=True) as cur:
        cur.execute(f"UPDATE products SET {field} = ? WHERE id = ?", (value, product_id))


def toggle_active(product_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("SELECT active FROM products WHERE id = ?", (product_id,))
        row = cur.fetchone()
        if row:
            new_value = 0 if row["active"] else 1
            cur.execute("UPDATE products SET active = ? WHERE id = ?", (new_value, product_id))


def has_orders(product_id: int) -> bool:
    """Verifica se o produto já foi usado em algum pedido (histórico de vendas)."""
    with database.get_cursor() as cur:
        cur.execute("SELECT 1 FROM orders WHERE product_id = ? LIMIT 1", (product_id,))
        return cur.fetchone() is not None


def delete(product_id: int) -> bool:
    """Exclui o produto definitivamente.

    Se o produto já tiver pedidos vinculados, a exclusão é bloqueada pela
    integridade do banco (para preservar o histórico de vendas). Nesse caso,
    o produto é apenas desativado em vez de removido, e a função retorna
    False para indicar que houve essa troca. Retorna True quando a exclusão
    definitiva foi concluída com sucesso.
    """
    if has_orders(product_id):
        with database.get_cursor(commit=True) as cur:
            cur.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
        return False

    with database.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM product_photos WHERE product_id = ?", (product_id,))
        cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    return True


# ---------------------------------------------------------------------------
# Fotos do produto
# ---------------------------------------------------------------------------
def add_photo(product_id: int, file_id: str, media_type: str = "photo") -> ProductPhoto:
    with database.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO product_photos (product_id, file_id, media_type) VALUES (?, ?, ?)",
            (product_id, file_id, media_type),
        )
        cur.execute("SELECT * FROM product_photos WHERE id = ?", (cur.lastrowid,))
        return ProductPhoto.from_row(cur.fetchone())


def list_photos(product_id: int) -> list[ProductPhoto]:
    with database.get_cursor() as cur:
        cur.execute("SELECT * FROM product_photos WHERE product_id = ?", (product_id,))
        return [ProductPhoto.from_row(r) for r in cur.fetchall()]


def clear_photos(product_id: int) -> None:
    with database.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM product_photos WHERE product_id = ?", (product_id,))


def count_all() -> int:
    with database.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM products")
        return cur.fetchone()["total"]
