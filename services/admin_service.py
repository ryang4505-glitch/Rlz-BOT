"""Regras de negócio relacionadas a administradores."""

import config
import database


def is_admin(telegram_id: int) -> bool:
    """Verifica se o telegram_id pertence a um administrador (env ou tabela admins)."""
    if telegram_id in config.ADMIN_IDS:
        return True
    with database.get_cursor() as cur:
        cur.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,))
        return cur.fetchone() is not None
