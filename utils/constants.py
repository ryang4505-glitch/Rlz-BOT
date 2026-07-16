"""Constantes e enums usados em todo o projeto (status, tipos de entrega, callbacks)."""

# ---------------------------------------------------------------------------
# Status de pedido
# ---------------------------------------------------------------------------
ORDER_AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
ORDER_AGUARDANDO_APROVACAO = "aguardando_aprovacao"
ORDER_APROVADO = "aprovado"
ORDER_RECUSADO = "recusado"
ORDER_ENTREGUE = "entregue"

ORDER_STATUS_LABELS = {
    ORDER_AGUARDANDO_PAGAMENTO: "⏳ Aguardando pagamento",
    ORDER_AGUARDANDO_APROVACAO: "🔎 Comprovante em análise",
    ORDER_APROVADO: "✅ Pagamento aprovado",
    ORDER_RECUSADO: "❌ Pagamento recusado",
    ORDER_ENTREGUE: "📦 Produto entregue",
}

# ---------------------------------------------------------------------------
# Status de pagamento
# ---------------------------------------------------------------------------
PAYMENT_PENDENTE = "pendente"
PAYMENT_APROVADO = "aprovado"
PAYMENT_RECUSADO = "recusado"

# ---------------------------------------------------------------------------
# Status de grupo
# ---------------------------------------------------------------------------
GROUP_PENDING = "pending"
GROUP_AUTHORIZED = "authorized"
GROUP_BLOCKED = "blocked"

GROUP_STATUS_LABELS = {
    GROUP_PENDING: "🕓 Pendente",
    GROUP_AUTHORIZED: "✅ Autorizado",
    GROUP_BLOCKED: "🚫 Bloqueado",
}

# ---------------------------------------------------------------------------
# Tipos de entrega de produtos digitais
# ---------------------------------------------------------------------------
DELIVERY_ARQUIVO = "arquivo"
DELIVERY_LINK = "link"
DELIVERY_TEXTO = "texto"
DELIVERY_CODIGO = "codigo"
DELIVERY_LICENCA = "licenca"
DELIVERY_CONVITE = "convite"

DELIVERY_TYPE_LABELS = {
    DELIVERY_ARQUIVO: "📁 Arquivo",
    DELIVERY_LINK: "🔗 Link",
    DELIVERY_TEXTO: "📝 Texto",
    DELIVERY_CODIGO: "🔑 Código",
    DELIVERY_LICENCA: "📜 Licença",
    DELIVERY_CONVITE: "📨 Convite de grupo/canal",
}

# ---------------------------------------------------------------------------
# Chaves de configuração (tabela settings)
# ---------------------------------------------------------------------------
SETTING_PIX_KEY = "pix_key"
SETTING_PIX_NAME = "pix_name"
SETTING_SUPPORT_TEXT = "support_text"

# ---------------------------------------------------------------------------
# Intervalos de divulgação automática (minutos)
# ---------------------------------------------------------------------------
BROADCAST_INTERVALS = [5, 10, 15, 30, 60]
