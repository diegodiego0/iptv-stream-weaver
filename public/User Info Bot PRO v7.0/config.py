# ══════════════════════════════════════════════
# ⚙️  CONFIG — User Info Bot PRO v7.0 (modular)
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Configurações centralizadas. Todos os módulos importam daqui.
Os arquivos JSON (banco, lang, log) ficam na MESMA pasta deste arquivo.
"""

import os
import re

# ── Credenciais Telegram ──
API_ID      = 29214781
API_HASH    = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE       = "+5588998225077"
BOT_TOKEN   = "8618840827:AAHohLnNTWh_lkP4l9du6KJTaRQcPsNrwV8"
OWNER_ID    = 2061557102
BOT_USERNAME = "InforUser_Bot"

# ── Caminhos (na mesma pasta deste arquivo) ──
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FOLDER_PATH  = os.path.join(BASE_DIR, "data")
FILE_PATH    = os.path.join(FOLDER_PATH, "user_database.json")
LOG_PATH     = os.path.join(FOLDER_PATH, "monitor.log")
LANG_FILE    = os.path.join(BASE_DIR, "lang.json")
COMBO_QUOTA_FILE = os.path.join(FOLDER_PATH, "combo_quota.json")
SESSION_USER = os.path.join(BASE_DIR, "session_monitor")
SESSION_BOT  = os.path.join(BASE_DIR, "session_bot")

os.makedirs(FOLDER_PATH, exist_ok=True)

# ── Parâmetros gerais ──
ITEMS_PER_PAGE = 8
SCAN_INTERVAL  = 3600
MAX_HISTORY    = 50

# ── Limites diários de COMBO (linhas usuario:senha) ──
# Free: 300 linhas/dia (totais, dos grupos do usuário)
# Premium: 800 dos grupos do usuário + 200 adicionais de outros grupos
#          = 1000 linhas/dia. Se grupos do usuário não atingirem 800,
#          o restante é completado com linhas de outros grupos até 1000.
DAILY_LIMIT_FREE              = 300
DAILY_LIMIT_PREMIUM_OWN       = 800
DAILY_LIMIT_PREMIUM_EXTRA     = 200
DAILY_LIMIT_PREMIUM_TOTAL     = DAILY_LIMIT_PREMIUM_OWN + DAILY_LIMIT_PREMIUM_EXTRA  # 1000

# ── Raspagem (rápida) ──
SCRAPE_MSG_LIMIT_PER_GROUP = 400   # mensagens vasculhadas por grupo
SCRAPE_CONCURRENCY         = 6     # grupos processados em paralelo

# ── Módulos premium ──
PREMIUM_MODULES = {
    "phone_full":      "☎️ Telefone 100%",
    "pagination_full": "🗂 Paginação Completa",
    "bio":             "🖊 Bio",
    "groups_full":     "✅ Ver todos os grupos",
    "combo":           "📋 Gerar combo",
}

# ── Padrões para extrair credenciais Xtream Codes ──
# Exemplos cobertos:
#   http://host:port/USER/PASS/
#   http://host:port/USER/PASS/12345
#   http://host:port/get.php?username=USER&password=PASS&...
#   http://host:port/player_api.php?username=USER&password=PASS
#   http://host/c/?username=USER&password=PASS
XTREAM_PATTERNS = [
    re.compile(
        r'https?://[^\s/"\'<>]+(?::\d+)?/'
        r'(?:get\.php|player_api\.php|panel_api\.php|xmltv\.php|c/?)?'
        r'\??[^\s"\'<>]*?username=([^\s&"\'<>]+)[^\s"\'<>]*?password=([^\s&"\'<>]+)',
        re.IGNORECASE,
    ),
    re.compile(
        r'https?://[^\s/"\'<>]+(?::\d+)?/'
        r'\??[^\s"\'<>]*?password=([^\s&"\'<>]+)[^\s"\'<>]*?username=([^\s&"\'<>]+)',
        re.IGNORECASE,
    ),
    # Path style: host:port/USER/PASS  (evita capturar player_api/xmltv)
    re.compile(
        r'https?://[^\s/"\'<>]+(?::\d+)?/'
        r'(?!get\.php|player_api\.php|panel_api\.php|xmltv\.php|c/)'
        r'([A-Za-z0-9_\-\.]{3,})/([A-Za-z0-9_\-\.]{3,})(?:[/?\s]|$)',
    ),
]

DEFAULT_HIDDEN = {"phone": False, "id": False, "username": False, "bio": False}

# ── Inline search: SOMENTE @username do usuário alvo ──
# v7+ : `@InforUser_Bot @nomeusuario`  (sem ID, sem nome)
BOT_INLINE_PATTERN = re.compile(
    r'^@?' + re.escape(BOT_USERNAME) + r'\s+@?([A-Za-z][A-Za-z0-9_]{3,31})\s*$',
    re.IGNORECASE,
)
