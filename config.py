"""
config.py
----------
Carrega e centraliza todas as configurações do bot a partir do arquivo .env.
Nenhum valor sensível deve ser escrito diretamente no código-fonte.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env que estiver na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _parse_admin_ids(raw: str) -> list[int]:
    """Converte a string 'ADMIN_IDS=123,456' em uma lista de inteiros."""
    if not raw:
        return []
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


# ---------------------------------------------------------------------------
# Configurações obrigatórias
# ---------------------------------------------------------------------------
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

# ---------------------------------------------------------------------------
# Configurações opcionais
# ---------------------------------------------------------------------------
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "database" / "shop.db"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "bot.log"))
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")  # usado para gerar links de divulgação

# Intervalos permitidos (em minutos) para as promoções automáticas
ALLOWED_INTERVALS: list[int] = [5, 10, 15, 30, 60]


def validate_config() -> None:
    """Valida se as configurações essenciais foram definidas antes de iniciar o bot."""
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN não foi definido no arquivo .env")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS não foi definido no arquivo .env (é necessário ao menos 1 administrador)")

    if errors:
        raise RuntimeError(
            "Configuração inválida:\n- " + "\n- ".join(errors) +
            "\n\nVerifique o arquivo .env (use o .env.example como base)."
        )
