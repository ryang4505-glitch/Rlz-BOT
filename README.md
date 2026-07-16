# 🤖 Bot de Loja Digital para Telegram

Bot profissional de vendas para Telegram, feito em **Python 3.12+**, com:

- Catálogo de produtos 100% digitais (sem frete, sem estoque físico).
- Atendimento e navegação totalmente por **botões** (sem comandos para o cliente).
- Pagamento via **Pix** com envio e aprovação manual de comprovante.
- **Entrega automática** do conteúdo após aprovação do pagamento.
- **Divulgação automática** e recorrente em grupos autorizados, usando **APScheduler**.
- **Painel administrativo** completo, restrito a IDs autorizados.
- Banco de dados **SQLite**, criado automaticamente e **totalmente vazio** — nenhum
  produto, categoria, promoção, chave Pix ou dado de teste é criado pelo projeto.
  Tudo é cadastrado por você, pelo próprio painel administrativo, dentro do Telegram.

---

## 📁 Estrutura do projeto

```
telegram_shop_bot/
├── main.py                 # Ponto de entrada do bot
├── config.py                # Leitura e validação das variáveis de ambiente
├── database.py               # Conexão SQLite + criação do schema
├── requirements.txt
├── .env.example
├── README.md
├── database/                 # Onde o arquivo shop.db é criado (git-ignored)
├── models/                   # Dataclasses tipadas (Product, Category, Order...)
├── services/                  # Regras de negócio (CRUD, entrega, divulgação...)
├── handlers/
│   ├── client/                # Handlers do cliente (menu, catálogo, compra...)
│   ├── admin/                 # Handlers do painel administrativo
│   ├── group_events.py        # Detecção automática de grupos
│   └── input_router.py        # Roteador central de texto/mídia por fluxo
└── utils/                     # Constantes, teclados, logger, decorators
```

---

## ✅ Pré-requisitos

- Python 3.12 ou superior instalado.
- Uma conta no Telegram.
- Um bot criado com o [@BotFather](https://t.me/BotFather) (para obter o `BOT_TOKEN`).

---

## 1. Instalar as dependências

Recomenda-se usar um ambiente virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## 2. Criar o bot e obter o token do Telegram

1. Abra o Telegram e converse com o **@BotFather**.
2. Envie `/newbot` e siga as instruções (nome e username do bot).
3. O BotFather vai te enviar um **token**, algo como:
   `123456789:ABCDefGhIJKlmNoPQRstuVwXyZ`
4. Guarde esse token — você vai usá-lo no próximo passo.

---

## 3. Configurar o arquivo `.env`

Copie o arquivo de exemplo:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Abra o `.env` e preencha:

```env
BOT_TOKEN=coloque_aqui_o_token_do_botfather
ADMIN_IDS=123456789,987654321
DB_PATH=database/shop.db
LOG_LEVEL=INFO
LOG_FILE=bot.log
BOT_USERNAME=nome_do_seu_bot_sem_arroba
```

- **BOT_TOKEN**: token recebido do @BotFather.
- **ADMIN_IDS**: IDs numéricos do Telegram de quem poderá acessar o painel
  administrativo, separados por vírgula. Para descobrir o seu ID, fale com o
  **@userinfobot** no Telegram.
- **BOT_USERNAME**: username do seu bot (sem `@`). Usado para montar os links
  do botão "🛒 Comprar Agora" enviados nos grupos.

---

## 4. Iniciar o bot

```bash
python main.py
```

Na primeira execução, o bot vai:

- Criar automaticamente o arquivo `database/shop.db` (SQLite), **vazio**.
- Sincronizar os administradores definidos em `ADMIN_IDS` na tabela `admins`.
- Começar a escutar mensagens (modo polling).

O banco **não vem com nenhum produto, categoria, promoção ou chave Pix**.
Você mesmo deverá cadastrar tudo pelo painel administrativo, descrito abaixo.

---

## 5. Como adicionar o bot em grupos

1. No Telegram, abra o grupo desejado.
2. Adicione o seu bot como membro do grupo.
3. O bot detecta automaticamente que foi adicionado e registra o grupo como
   **pendente**.
4. Todos os administradores configurados em `ADMIN_IDS` recebem uma notificação
   privada avisando sobre o novo grupo.
5. Vá até **Painel → Grupos** e clique em **Autorizar** para liberar esse grupo
   a receber as divulgações automáticas das promoções.

> Se o bot for removido do grupo, ele é automaticamente marcado como
> "bloqueado" no painel.

---

## 6. Como usar o painel administrativo

No Telegram, converse diretamente com o seu bot (no privado) e envie:

```
/admin
```

ou

```
/painel
```

Apenas os IDs listados em `ADMIN_IDS` (ou cadastrados na tabela `admins`)
conseguem acessar. Você verá um menu com botões para:

| Opção | O que faz |
|---|---|
| 📦 Produtos | Cadastrar, editar, ativar/desativar e excluir produtos digitais |
| 🗂 Categorias | Cadastrar, editar, ativar/desativar e excluir categorias |
| 🔥 Promoções | Criar promoções de divulgação automática e ativar/pausar o envio |
| 👥 Grupos | Ver grupos detectados, autorizar, bloquear ou remover |
| 💠 Pix | Configurar a chave Pix e o nome do titular usados nas cobranças |
| 🧾 Pedidos | Ver pedidos, aprovar ou recusar comprovantes de pagamento |
| 🙋 Clientes | Ver os clientes que já interagiram com o bot |
| 📊 Estatísticas | Ver números gerais da loja (vendas, pedidos, grupos, etc.) |

### Cadastrando um produto

1. **Painel → Produtos → ➕ Adicionar produto**.
2. Informe nome, descrição, categoria (é necessário ter ao menos uma categoria
   criada antes), preço, método de entrega e, por fim, envie as fotos do
   produto.
3. Métodos de entrega disponíveis: **arquivo**, **link**, **texto**,
   **código**, **licença** ou **convite de grupo/canal**. Você escolhe qual se
   aplica a cada produto — o conteúdo correspondente é entregue automaticamente
   ao cliente assim que o pagamento for aprovado.

### Criando uma promoção de divulgação automática

1. **Painel → Promoções → ➕ Criar promoção**.
2. Defina um nome interno, o texto de divulgação, uma imagem (opcional), o
   produto vinculado (opcional — o botão "🛒 Comprar Agora" leva o cliente
   direto para esse produto no privado do bot) e o intervalo de envio:
   **5, 10, 15, 30 ou 60 minutos**.
3. Depois de criada, abra a promoção na lista e toque em **▶️ Ativar
   divulgação** para começar o envio automático a todos os grupos
   autorizados.

### Aprovando um pagamento

1. Quando um cliente compra um produto, ele recebe as instruções de pagamento
   com a chave Pix configurada.
2. Ao enviar o comprovante (foto ou arquivo) no chat com o bot, todos os
   administradores recebem uma notificação com os dados do pedido e o
   comprovante anexado.
3. Toque em **✅ Aprovar pagamento** para liberar a entrega automática do
   produto ao cliente, ou em **❌ Recusar pagamento** caso o comprovante não
   seja válido.

---

## 🗃 Estrutura do banco de dados (SQLite)

| Tabela | Descrição |
|---|---|
| `admins` | Administradores autorizados (sincronizado a partir do `.env`) |
| `customers` | Clientes que interagiram com o bot |
| `categories` | Categorias de produtos |
| `products` | Produtos digitais |
| `product_photos` | Fotos vinculadas a cada produto |
| `promotions` | Promoções de divulgação automática |
| `groups` | Grupos/canais onde o bot foi adicionado |
| `orders` | Pedidos realizados pelos clientes |
| `payments` | Comprovantes de pagamento enviados e seu status |
| `settings` | Configurações gerais (ex: chave Pix) |

---

## 🔒 Observações de segurança

- Nunca compartilhe o seu `BOT_TOKEN` nem o arquivo `.env`.
- Apenas os IDs listados em `ADMIN_IDS` têm acesso ao painel administrativo.
- Faça backups periódicos do arquivo `database/shop.db`.

---

## 🛠 Manutenção e logs

- Os logs são gravados tanto no console quanto no arquivo definido em
  `LOG_FILE` (rotacionado automaticamente).
- O código está organizado em módulos (`models`, `services`, `handlers`,
  `utils`) para facilitar manutenção e extensão futura.
