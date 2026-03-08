# ══════════════════════════════════════════════════════════════════
# 🕵️  USER INFO BOT PRO v7.0 — MEGA PROFESSIONAL EDITION
# 👨‍💻  Criado por: Edivaldo Silva @Edkd1
# 🔖  Versão: 7.0 (773H Ultra)
# ══════════════════════════════════════════════════════════════════
#
#  FUNCIONALIDADES:
#  ✅ 100% do código original v5.0 preservado
#  ✅ Busca via @InforUser_Bot + termo/username/ID
#  ✅ Suporte a tópicos (topics) em grupos
#  ✅ Consulta via API Telegram (fallback)
#  ✅ Salva dados da API no banco para futuras consultas
#  ✅ Salva telefone do perfil quando disponível
#  ✅ Registra quem fez a consulta no banco
#  ✅ Status "digitando" durante consulta API
#  ✅ Notificações de alterações nos grupos (bot admin)
#  ✅ Exibição de regras do grupo
#  ✅ Saudação para novos membros (personalizável)
#  ✅ Controle de abuso (rate limit + avisos + ban)
#  ✅ Envio de abusos no DM do dono
#
# ══════════════════════════════════════════════════════════════════

import json
import os
import asyncio
import time
import re
from datetime import datetime
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChatAdminRequiredError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import (
    ChannelParticipantAdmin, ChannelParticipantCreator,
    ChatParticipantAdmin, ChatParticipantCreator,
    PeerChannel, PeerChat, InputPeerChannel,
    MessageActionChatAddUser, MessageActionChatJoinedByLink,
    MessageActionChatJoinedByRequest
)

# ══════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES
# ══════════════════════════════════════════════
API_ID = 29214781                        # Obtenha em https://my.telegram.org
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102                 # Edivaldo Silva @Edkd1
OWNER_USER = "@Edkd1"
OWNER_NAME = "Edivaldo Silva"

BOT_USERNAME = "InforUser_Bot"        # Username do bot (sem @)

FOLDER_PATH = "data"
FILE_PATH = os.path.join(FOLDER_PATH, "user_database.json")
LOG_PATH = os.path.join(FOLDER_PATH, "monitor.log")
CONFIG_PATH = os.path.join(FOLDER_PATH, "bot_config.json")
SESSION_USER = "session_monitor"
SESSION_BOT = "session_bot"

ITEMS_PER_PAGE = 10                   # 10 itens por página
SCAN_INTERVAL = 1800                  # Varredura a cada 30 min
MAX_HISTORY = 50
SCAN_BATCH_SIZE = 200                 # Participantes por lote
SCAN_BATCH_DELAY = 0.3               # Delay entre lotes
FLOOD_WAIT_MARGIN = 1.2              # Multiplicador de segurança para FloodWait

# ── Controle de Abuso ──
ABUSE_MAX_COMMANDS = 10               # Máx. comandos por janela
ABUSE_WINDOW = 60                     # Janela em segundos
ABUSE_WARN_THRESHOLD = 3             # Avisos antes de ban
ABUSE_BAN_DURATION = 3600            # Ban temporário (1h)

BOT_VERSION = "7.0"
BOT_CODENAME = "773H Ultra"

# ══════════════════════════════════════════════
# 📁  BANCO DE DADOS JSON — CRIAÇÃO AUTOMÁTICA
# ══════════════════════════════════════════════
os.makedirs(FOLDER_PATH, exist_ok=True)

def inicializar_banco():
    """Cria o banco de dados na primeira execução com estrutura padrão."""
    if not os.path.exists(FILE_PATH):
        estrutura_inicial = {
            "_meta": {
                "versao": BOT_VERSION,
                "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "total_varreduras": 0,
                "ultimo_scan": None
            }
        }
        salvar_dados(estrutura_inicial)
        log("🆕 Banco de dados criado com sucesso na primeira execução!")
        return True
    return False

def carregar_dados() -> dict:
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"_meta": {"versao": BOT_VERSION, "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}
    return {"_meta": {"versao": BOT_VERSION, "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}

def salvar_dados(db: dict):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar banco: {e}")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except IOError:
        pass

# ══════════════════════════════════════════════
# 📋  CONFIGURAÇÃO DINÂMICA (TÓPICOS, SAUDAÇÕES)
# ══════════════════════════════════════════════

def carregar_config() -> dict:
    """Carrega configurações do bot (tópicos, saudações, bans)."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "topics": {},           # {chat_id: topic_id}
        "welcome_msgs": {},     # {chat_id: "mensagem"}
        "banned_users": {},     # {user_id: {"until": timestamp, "reason": str}}
        "abuse_warnings": {},   # {user_id: count}
        "admin_groups": []      # [chat_id, ...]
    }

def salvar_config(cfg: dict):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar config: {e}")

# ══════════════════════════════════════════════
# 🤖  CLIENTES TELETHON
# ══════════════════════════════════════════════
user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot = TelegramClient(SESSION_BOT, API_ID, API_HASH)

# Estado global
scan_running = False
operation_lock = asyncio.Lock()       # Lock para evitar conflitos entre operações
scan_paused = False                   # Flag para pausar varredura durante outras operações
scan_stats = {"last_scan": None, "users_scanned": 0, "groups_scanned": 0, "changes_detected": 0}

# Controle de abuso
abuse_tracker = defaultdict(list)     # {user_id: [timestamps]}

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID

# ══════════════════════════════════════════════
# 🛡️  CONTROLE DE ABUSO
# ══════════════════════════════════════════════

def verificar_abuso(user_id: int) -> tuple:
    """
    Verifica se o usuário está abusando do bot.
    Returns: (is_abusing: bool, is_banned: bool, msg: str)
    """
    if user_id == OWNER_ID:
        return False, False, ""

    cfg = carregar_config()
    agora = time.time()

    # Verifica ban ativo
    ban_info = cfg.get("banned_users", {}).get(str(user_id))
    if ban_info:
        until = ban_info.get("until", 0)
        if until > agora:
            remaining = int(until - agora)
            mins = remaining // 60
            return False, True, f"🚫 Você está banido por mais **{mins} minuto(s)**.\nMotivo: _{ban_info.get('reason', 'Abuso')}_"
        else:
            # Ban expirou
            del cfg["banned_users"][str(user_id)]
            salvar_config(cfg)

    # Rate limiting
    timestamps = abuse_tracker[user_id]
    timestamps = [t for t in timestamps if agora - t < ABUSE_WINDOW]
    abuse_tracker[user_id] = timestamps

    if len(timestamps) >= ABUSE_MAX_COMMANDS:
        warnings = cfg.get("abuse_warnings", {}).get(str(user_id), 0) + 1
        if "abuse_warnings" not in cfg:
            cfg["abuse_warnings"] = {}
        cfg["abuse_warnings"][str(user_id)] = warnings

        if warnings >= ABUSE_WARN_THRESHOLD:
            # Banir temporariamente
            if "banned_users" not in cfg:
                cfg["banned_users"] = {}
            cfg["banned_users"][str(user_id)] = {
                "until": agora + ABUSE_BAN_DURATION,
                "reason": f"Excesso de comandos ({warnings} avisos)",
                "banned_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            cfg["abuse_warnings"][str(user_id)] = 0
            salvar_config(cfg)
            return True, True, f"🚫 Você foi **banido temporariamente** por {ABUSE_BAN_DURATION // 60} minutos devido a uso excessivo."
        else:
            salvar_config(cfg)
            return True, False, f"⚠️ **Aviso {warnings}/{ABUSE_WARN_THRESHOLD}** — Você está enviando comandos muito rápido!\nAguarde alguns segundos antes de continuar."

    # Registra comando
    abuse_tracker[user_id].append(agora)
    return False, False, ""


async def notificar_abuso(user_id: int, user_name: str, action: str, details: str = ""):
    """Notifica o dono sobre abuso no DM."""
    try:
        cfg = carregar_config()
        warnings = cfg.get("abuse_warnings", {}).get(str(user_id), 0)
        ban_info = cfg.get("banned_users", {}).get(str(user_id))

        text = f"""🚨 **ALERTA DE ABUSO**

━━━━━━━━━━━━━━━━━━━━━
👤 **Usuário:** `{user_name}`
🔢 **ID:** `{user_id}`
⚠️ **Ação:** {action}
📊 **Avisos acumulados:** {warnings}/{ABUSE_WARN_THRESHOLD}
"""
        if ban_info:
            text += f"🚫 **Status:** BANIDO até `{datetime.fromtimestamp(ban_info['until']).strftime('%d/%m/%Y %H:%M:%S')}`\n"

        if details:
            text += f"\n📝 **Detalhes:** {details}\n"

        text += f"""
━━━━━━━━━━━━━━━━━━━━━
🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`"""

        btns = [
            [Button.inline("⚠️ Enviar Aviso", f"abuse_warn_{user_id}".encode()),
             Button.inline("🚫 Banir 1h", f"abuse_ban_{user_id}_3600".encode())],
            [Button.inline("🚫 Banir 24h", f"abuse_ban_{user_id}_86400".encode()),
             Button.inline("✅ Desbanir", f"abuse_unban_{user_id}".encode())],
            [Button.inline("📋 Ver Interações", f"abuse_log_{user_id}".encode())]
        ]

        await bot.send_message(OWNER_ID, text, parse_mode='md', buttons=btns)
    except Exception as e:
        log(f"❌ Erro ao notificar abuso: {e}")

# ══════════════════════════════════════════════
# 📱  REGISTRO COM TELEFONE + INTERAÇÃO
# ══════════════════════════════════════════════

async def registrar_interacao(event):
    """Registra automaticamente o usuário que interage com o bot no banco."""
    try:
        user = await event.get_sender()
        if not user or getattr(user, 'bot', False):
            return
        uid = str(user.id)
        db = carregar_dados()
        nome = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome"
        username = f"@{user.username}" if user.username else "Nenhum"
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Captura telefone se disponível
        phone = getattr(user, 'phone', None)
        phone_str = f"+{phone}" if phone else None

        if uid not in db:
            entry = {
                "id": user.id,
                "nome_atual": nome,
                "username_atual": username,
                "grupos": [],
                "primeiro_registro": agora,
                "historico": [],
                "origem": "interacao_bot"
            }
            if phone_str:
                entry["telefone"] = phone_str
            db[uid] = entry
            salvar_dados(db)
            log(f"➕ Novo usuário registrado via interação: {nome} ({uid})")
        else:
            changed = False
            if db[uid]["nome_atual"] != nome:
                db[uid]["historico"].append({
                    "data": agora, "tipo": "NOME",
                    "de": db[uid]["nome_atual"], "para": nome,
                    "grupo": "Bot DM"
                })
                db[uid]["nome_atual"] = nome
                changed = True
            if db[uid]["username_atual"] != username:
                db[uid]["historico"].append({
                    "data": agora, "tipo": "USER",
                    "de": db[uid]["username_atual"], "para": username,
                    "grupo": "Bot DM"
                })
                db[uid]["username_atual"] = username
                changed = True
            # Atualiza telefone se obtido
            if phone_str and db[uid].get("telefone") != phone_str:
                db[uid]["telefone"] = phone_str
                changed = True
            if changed:
                if len(db[uid]["historico"]) > MAX_HISTORY:
                    db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]
                salvar_dados(db)
    except Exception as e:
        log(f"⚠️ Erro ao registrar interação: {e}")

# ══════════════════════════════════════════════
# 🌐  CONSULTA VIA API TELEGRAM (FALLBACK)
# ══════════════════════════════════════════════

async def consultar_api_telegram(query: str, event=None) -> dict:
    """
    Consulta usuário via API do Telegram quando não encontrado no banco.
    Mantém status 'digitando' durante a consulta.
    Salva resultado no banco para futuras consultas.
    """
    resultado = None

    try:
        # Mantém status "digitando"
        if event:
            chat = await event.get_chat()
            asyncio.create_task(_manter_digitando(chat.id, event))

        entity = None
        query_clean = query.strip().lstrip('@')

        # Tenta resolver por username
        if not query_clean.isdigit():
            try:
                entity = await user_client.get_entity(query_clean)
            except Exception:
                try:
                    entity = await user_client.get_entity(f"@{query_clean}")
                except Exception:
                    pass
        else:
            # Tenta por ID
            try:
                entity = await user_client.get_entity(int(query_clean))
            except Exception:
                pass

        if not entity:
            return None

        # Obtém informações completas
        try:
            full = await user_client(GetFullUserRequest(entity))
            full_user = full.full_user
        except Exception:
            full_user = None

        uid = str(entity.id)
        nome = f"{entity.first_name or ''} {entity.last_name or ''}".strip() or "Sem nome"
        username = f"@{entity.username}" if entity.username else "Nenhum"
        phone = getattr(entity, 'phone', None)
        phone_str = f"+{phone}" if phone else None
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        bio = ""
        if full_user:
            bio = getattr(full_user, 'about', '') or ""

        resultado = {
            "id": entity.id,
            "nome_atual": nome,
            "username_atual": username,
            "bio": bio,
            "grupos": [],
            "primeiro_registro": agora,
            "historico": [],
            "origem": "api_telegram"
        }
        if phone_str:
            resultado["telefone"] = phone_str

        # Salva no banco para futuras consultas
        db = carregar_dados()
        if uid not in db:
            db[uid] = resultado
            salvar_dados(db)
            log(f"🌐 Usuário salvo via API: {nome} ({uid})")
        else:
            # Atualiza dados existentes com info da API
            changed = False
            if phone_str and not db[uid].get("telefone"):
                db[uid]["telefone"] = phone_str
                changed = True
            if bio and not db[uid].get("bio"):
                db[uid]["bio"] = bio
                changed = True
            if changed:
                salvar_dados(db)

        return resultado

    except Exception as e:
        log(f"⚠️ Erro na consulta API: {e}")
        return None


_digitando_ativo = {}

async def _manter_digitando(chat_id: int, event):
    """Mantém status 'digitando' até a consulta finalizar."""
    _digitando_ativo[chat_id] = True
    try:
        while _digitando_ativo.get(chat_id, False):
            try:
                async with bot.action(chat_id, 'typing'):
                    await asyncio.sleep(3)
            except Exception:
                break
    except Exception:
        pass

def _parar_digitando(chat_id: int):
    _digitando_ativo[chat_id] = False

# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════
async def notificar(texto: str):
    try:
        await bot.send_message(OWNER_ID, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")

# ══════════════════════════════════════════════
# 📣  NOTIFICAÇÃO EM GRUPOS (BOT ADMIN)
# ══════════════════════════════════════════════

async def notificar_grupo(chat_id: int, texto: str, topic_id: int = None):
    """Envia notificação no grupo onde o bot é admin, respeitando tópicos."""
    try:
        kwargs = {"parse_mode": "md"}
        if topic_id:
            kwargs["reply_to"] = topic_id
        await bot.send_message(chat_id, texto, **kwargs)
    except Exception as e:
        log(f"⚠️ Erro ao notificar grupo {chat_id}: {e}")


async def verificar_admin_bot(chat_id: int) -> bool:
    """Verifica se o bot é administrador no grupo."""
    try:
        me = await bot.get_me()
        participant = await bot.get_permissions(chat_id, me.id)
        return participant.is_admin if participant else False
    except Exception:
        return False

# ══════════════════════════════════════════════
# 🎨  INTERFACE — MENUS INLINE
# ══════════════════════════════════════════════

def menu_principal_buttons(user_id: int = 0):
    btns = [
        [Button.inline("🔍 Buscar Usuário", b"cmd_buscar"),
         Button.inline("📊 Estatísticas", b"cmd_stats")],
    ]
    if is_admin(user_id):
        btns.append(
            [Button.inline("🔄 Iniciar Varredura", b"cmd_scan"),
             Button.inline("📋 Últimas Alterações", b"cmd_recent")]
        )
        btns.append(
            [Button.inline("📤 Exportar Banco", b"cmd_export"),
             Button.inline("⚙️ Configurações", b"cmd_config")]
        )
        btns.append(
            [Button.inline("👥 Grupos do Usuário", b"cmd_grupos"),
             Button.inline("🗑️ Limpar Cache", b"cmd_clear_cache")]
        )
        btns.append(
            [Button.inline("📌 Configurar Tópico", b"cmd_set_topic"),
             Button.inline("👋 Config. Saudação", b"cmd_set_welcome")]
        )
        btns.append(
            [Button.inline("🛡️ Controle de Abuso", b"cmd_abuse_panel")]
        )
    else:
        btns.append(
            [Button.inline("📋 Últimas Alterações", b"cmd_recent")]
        )
    btns.append([Button.inline("ℹ️ Sobre", b"cmd_about")])
    return btns

def voltar_button():
    return [[Button.inline("🔙 Menu Principal", b"cmd_menu")]]

def paginar_buttons(prefix: str, page: int, total_pages: int):
    btns = []
    nav = []
    if page > 0:
        nav.append(Button.inline("⏮️ Primeira", f"{prefix}_page_0".encode()))
        nav.append(Button.inline("◀️ Anterior", f"{prefix}_page_{page - 1}".encode()))
    nav.append(Button.inline(f"📄 {page + 1}/{total_pages}", b"noop"))
    if page < total_pages - 1:
        nav.append(Button.inline("Próxima ▶️", f"{prefix}_page_{page + 1}".encode()))
        nav.append(Button.inline("⏭️ Última", f"{prefix}_page_{total_pages - 1}".encode()))
    btns.append(nav)
    # Navegação rápida — páginas intermediárias
    if total_pages > 5:
        quick_nav = []
        step = max(1, total_pages // 5)
        pages_to_show = set()
        for i in range(0, total_pages, step):
            pages_to_show.add(i)
        pages_to_show.add(total_pages - 1)
        pages_to_show.discard(page)
        for p in sorted(pages_to_show)[:5]:
            quick_nav.append(Button.inline(f"[{p + 1}]", f"{prefix}_page_{p}".encode()))
        if quick_nav:
            btns.append(quick_nav)
    btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])
    return btns

# ══════════════════════════════════════════════
# 🔍  BUSCA AVANÇADA
# ══════════════════════════════════════════════

def buscar_usuario(query: str) -> list:
    db = carregar_dados()
    query_lower = query.lower().lstrip('@')
    results = []

    for uid, dados in db.items():
        if uid.startswith("_"):
            continue
        if query == uid:
            results.append(dados)
            continue
        username = dados.get("username_atual", "").lower().lstrip('@')
        if username and query_lower == username:
            results.insert(0, dados)
            continue
        nome = dados.get("nome_atual", "").lower()
        if query_lower in nome or query_lower in username:
            results.append(dados)
        # Busca por telefone
        telefone = dados.get("telefone", "").replace("+", "")
        if telefone and query_lower.replace("+", "") in telefone:
            results.append(dados)

    return results

def formatar_perfil(dados: dict) -> str:
    uid = dados.get("id", "?")
    nome = dados.get("nome_atual", "Desconhecido")
    username = dados.get("username_atual", "Nenhum")
    historico = dados.get("historico", [])
    grupos = dados.get("grupos", [])
    total_changes = len(historico)
    telefone = dados.get("telefone", "Não disponível")
    bio = dados.get("bio", "")
    origem = dados.get("origem", "varredura")

    recent = historico[-5:]
    hist_text = ""
    for h in reversed(recent):
        emoji = "📛" if h.get("tipo") == "NOME" else "🆔"
        hist_text += f"  {emoji} `{h['data']}` — {h['de']} ➜ {h['para']}\n"

    if not hist_text:
        hist_text = "  _Nenhuma alteração registrada_\n"

    first_seen = dados.get("primeiro_registro", historico[0]["data"] if historico else "N/A")
    last_change = historico[-1]["data"] if historico else "N/A"

    # Mostrar grupos
    grupos_text = ""
    if grupos:
        for g in grupos[:10]:
            grupos_text += f"  • {g}\n"
        if len(grupos) > 10:
            grupos_text += f"  _... e mais {len(grupos) - 10} grupos_\n"
    else:
        grupos_text = "  _Nenhum grupo registrado_\n"

    bio_text = f"\n📝 **Bio:** _{bio}_" if bio else ""

    return f"""╔══════════════════════════╗
║  🕵️ **PERFIL DO USUÁRIO**  ║
╚══════════════════════════╝

👤 **Nome:** `{nome}`
🆔 **Username:** `{username}`
🔢 **ID:** `{uid}`
📱 **Telefone:** `{telefone}`{bio_text}
🏷️ **Origem:** _{origem}_

📊 **Resumo:**
├ 📝 Total de alterações: **{total_changes}**
├ 📅 Primeiro registro: `{first_seen}`
├ 🕐 Última alteração: `{last_change}`
└ 📂 Grupos: **{len(grupos)}**

📂 **Grupos onde está presente:**
{grupos_text}
📜 **Últimas Alterações:**
{hist_text}
_Créditos: {OWNER_USER}_"""

# ══════════════════════════════════════════════
# 📡  VARREDURA RÁPIDA DE GRUPOS
# ══════════════════════════════════════════════

async def executar_varredura(notify_chat=None):
    global scan_running, scan_paused, scan_stats
    if scan_running:
        if notify_chat:
            await bot.send_message(notify_chat, "⚠️ Uma varredura já está em andamento!")
        return

    # Adquire o lock para evitar conflitos
    async with operation_lock:
        scan_running = True
        scan_paused = False
        scan_stats = {"last_scan": None, "users_scanned": 0, "groups_scanned": 0, "changes_detected": 0}
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        scan_stats["last_scan"] = agora
        db = carregar_dados()
        cfg = carregar_config()

        # Atualiza meta
        if "_meta" in db:
            db["_meta"]["total_varreduras"] = db["_meta"].get("total_varreduras", 0) + 1
            db["_meta"]["ultimo_scan"] = agora

        if notify_chat:
            await bot.send_message(
                notify_chat,
                "🔄 **Varredura RÁPIDA iniciada...**\n\n"
                "⚡ Modo otimizado ativado\n"
                "⏳ Analisando grupos em lotes paralelos.\n"
                "Você será notificado ao finalizar.",
                parse_mode='md'
            )

        log("🔄 Varredura rápida iniciada")
        start_time = asyncio.get_event_loop().time()

        try:
            # Coleta todos os diálogos de uma vez
            dialogs = []
            async for dialog in user_client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    dialogs.append(dialog)

            log(f"📂 {len(dialogs)} grupos encontrados para varredura")

            for dialog in dialogs:
                # Pausa a varredura se alguém está usando o bot
                while scan_paused:
                    await asyncio.sleep(1)

                nome_grupo = dialog.name
                chat_id_grupo = dialog.id
                scan_stats["groups_scanned"] += 1

                # Verifica se o bot é admin neste grupo
                bot_is_admin = await verificar_admin_bot(chat_id_grupo)
                topic_id = cfg.get("topics", {}).get(str(chat_id_grupo))

                try:
                    participants = []
                    try:
                        async for user in user_client.iter_participants(dialog.id, limit=SCAN_BATCH_SIZE * 10):
                            if user.bot:
                                continue
                            participants.append(user)
                    except Exception:
                        continue

                    for user in participants:
                        uid = str(user.id)
                        nome_atual = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome"
                        user_atual = f"@{user.username}" if user.username else "Nenhum"
                        phone = getattr(user, 'phone', None)
                        phone_str = f"+{phone}" if phone else None
                        scan_stats["users_scanned"] += 1

                        if uid not in db:
                            entry = {
                                "id": user.id,
                                "nome_atual": nome_atual,
                                "username_atual": user_atual,
                                "grupos": [nome_grupo],
                                "primeiro_registro": agora,
                                "historico": []
                            }
                            if phone_str:
                                entry["telefone"] = phone_str
                            db[uid] = entry
                        else:
                            if uid.startswith("_"):
                                continue
                            # Atualiza lista de grupos
                            if "grupos" not in db[uid]:
                                db[uid]["grupos"] = []
                            if nome_grupo not in db[uid]["grupos"]:
                                db[uid]["grupos"].append(nome_grupo)

                            # Atualiza telefone
                            if phone_str and not db[uid].get("telefone"):
                                db[uid]["telefone"] = phone_str

                            # Detecta mudança de nome
                            if db[uid]["nome_atual"] != nome_atual:
                                scan_stats["changes_detected"] += 1
                                db[uid]["historico"].append({
                                    "data": agora,
                                    "tipo": "NOME",
                                    "de": db[uid]["nome_atual"],
                                    "para": nome_atual,
                                    "grupo": nome_grupo
                                })
                                change_text = (
                                    f"🔔 **ALTERAÇÃO DE NOME**\n\n"
                                    f"👤 ID: `{uid}`\n"
                                    f"❌ Antigo: `{db[uid]['nome_atual']}`\n"
                                    f"✅ Novo: `{nome_atual}`\n"
                                    f"📍 Grupo: _{nome_grupo}_"
                                )
                                await notificar(change_text)
                                # Notifica no grupo se bot é admin
                                if bot_is_admin:
                                    await notificar_grupo(
                                        chat_id_grupo,
                                        f"🔔 **Alteração detectada:**\n"
                                        f"👤 `{db[uid]['nome_atual']}` ➜ `{nome_atual}`\n"
                                        f"🆔 ID: `{uid}`",
                                        topic_id=topic_id
                                    )
                                db[uid]["nome_atual"] = nome_atual

                            # Detecta mudança de username
                            if db[uid]["username_atual"] != user_atual:
                                scan_stats["changes_detected"] += 1
                                db[uid]["historico"].append({
                                    "data": agora,
                                    "tipo": "USER",
                                    "de": db[uid]["username_atual"],
                                    "para": user_atual,
                                    "grupo": nome_grupo
                                })
                                change_text = (
                                    f"🆔 **MUDANÇA DE USERNAME**\n\n"
                                    f"👤 Nome: `{nome_atual}`\n"
                                    f"❌ Antigo: `{db[uid]['username_atual']}`\n"
                                    f"✅ Novo: `{user_atual}`\n"
                                    f"📍 Grupo: _{nome_grupo}_"
                                )
                                await notificar(change_text)
                                if bot_is_admin:
                                    await notificar_grupo(
                                        chat_id_grupo,
                                        f"🆔 **Username alterado:**\n"
                                        f"👤 `{db[uid]['username_atual']}` ➜ `{user_atual}`\n"
                                        f"🔢 ID: `{uid}`",
                                        topic_id=topic_id
                                    )
                                db[uid]["username_atual"] = user_atual

                            # Limita histórico
                            if len(db[uid]["historico"]) > MAX_HISTORY:
                                db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]

                    await asyncio.sleep(SCAN_BATCH_DELAY)

                except FloodWaitError as e:
                    wait_time = int(e.seconds * FLOOD_WAIT_MARGIN)
                    log(f"⏳ FloodWait: aguardando {wait_time}s")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    log(f"⚠️ Erro no grupo {nome_grupo}: {e}")
                    continue

        except Exception as e:
            log(f"❌ Erro na varredura: {e}")
        finally:
            salvar_dados(db)
            scan_running = False
            elapsed = asyncio.get_event_loop().time() - start_time
            log(f"✅ Varredura concluída em {elapsed:.1f}s: {scan_stats['groups_scanned']} grupos, "
                f"{scan_stats['users_scanned']} usuários, {scan_stats['changes_detected']} alterações")

        if notify_chat:
            await bot.send_message(
                notify_chat,
                f"""✅ **Varredura Concluída!**

╔═══════════════════════╗
║  📊 **RESULTADO**       ║
╚═══════════════════════╝

⚡ Tempo: **{elapsed:.1f} segundos**
📂 Grupos analisados: **{scan_stats['groups_scanned']}**
👥 Usuários verificados: **{scan_stats['users_scanned']}**
🔔 Alterações detectadas: **{scan_stats['changes_detected']}**
🕐 Horário: `{agora}`

_Próxima varredura automática em {SCAN_INTERVAL // 60} min_
_Créditos: {OWNER_USER}_""",
                parse_mode='md',
                buttons=voltar_button()
            )

# ══════════════════════════════════════════════
# 🏠  REGRAS DO GRUPO
# ══════════════════════════════════════════════

async def obter_regras_grupo(chat_id: int) -> str:
    """Obtém as regras/descrição do grupo."""
    try:
        chat = await bot.get_entity(chat_id)
        if hasattr(chat, 'megagroup') and chat.megagroup:
            full = await bot(GetFullChannelRequest(chat))
            about = full.full_chat.about or ""
        else:
            full = await bot(GetFullChatRequest(chat.id))
            about = full.full_chat.about or ""

        if about:
            return about
        return "📋 Este grupo não possui regras definidas na descrição."
    except Exception as e:
        log(f"⚠️ Erro ao obter regras: {e}")
        return "❌ Não foi possível obter as regras do grupo."

# ══════════════════════════════════════════════
# 📌  HELPERS PARA TÓPICOS
# ══════════════════════════════════════════════

def get_reply_kwargs(event, cfg: dict = None) -> dict:
    """
    Retorna kwargs para responder no tópico correto.
    Se o evento veio de um tópico, responde nele.
    Se há tópico configurado para o grupo, usa ele.
    """
    kwargs = {"parse_mode": "md"}
    chat_id = event.chat_id

    # Se a mensagem já está em um tópico (reply_to com forum topic)
    if hasattr(event, 'reply_to') and event.reply_to:
        topic_id = getattr(event.reply_to, 'reply_to_top_id', None) or getattr(event.reply_to, 'reply_to_msg_id', None)
        if topic_id:
            kwargs["reply_to"] = topic_id
            return kwargs

    # Verifica tópico configurado
    if cfg is None:
        cfg = carregar_config()
    configured_topic = cfg.get("topics", {}).get(str(chat_id))
    if configured_topic:
        kwargs["reply_to"] = configured_topic

    return kwargs

async def responder_evento(event, text: str, buttons=None, cfg=None):
    """Responde ao evento no tópico correto, mencionando o usuário."""
    kwargs = get_reply_kwargs(event, cfg)
    if buttons:
        kwargs["buttons"] = buttons

    # Menciona o usuário que fez o comando
    sender = await event.get_sender()
    if sender and not event.is_private:
        mention = f"[{sender.first_name or 'Usuário'}](tg://user?id={sender.id})"
        text = f"👤 {mention}\n\n{text}"

    await event.reply(text, **kwargs)

# ══════════════════════════════════════════════
# 🎮  HANDLERS DO BOT
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)

    # Verificar abuso
    sender = await event.get_sender()
    if sender:
        is_abusing, is_banned, abuse_msg = verificar_abuso(sender.id)
        if is_banned:
            await event.reply(abuse_msg, parse_mode='md')
            scan_paused = False
            return
        if is_abusing:
            await event.reply(abuse_msg, parse_mode='md')
            await notificar_abuso(sender.id, f"{sender.first_name}", "Flood de /start")
            scan_paused = False
            return

    uid = sender.id if sender else 0
    await responder_evento(
        event,
        f"""╔══════════════════════════════╗
║  🕵️ **User Info Bot Pro v{BOT_VERSION}**  ║
╚══════════════════════════════╝

Bem-vindo ao monitor profissional de usuários!

🔍 **Busque** por ID, @username ou nome
📊 **Monitore** alterações em tempo real
📜 **Histórico** completo de mudanças
📂 **Grupos** onde o usuário está presente
📱 **Telefone** capturado automaticamente
🌐 **API Telegram** como fallback inteligente

━━━━━━━━━━━━━━━━━━━━━
💡 **Dica:** Use `@{BOT_USERNAME} termo` em qualquer chat!
━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: {OWNER_NAME} {OWNER_USER}_
⚡ _Powered by {BOT_CODENAME} — v{BOT_VERSION}_
━━━━━━━━━━━━━━━━━━━━━

Selecione uma opção abaixo:""",
        buttons=menu_principal_buttons(uid)
    )
    scan_paused = False

@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await registrar_interacao(event)
    await cmd_start(event)

@bot.on(events.NewMessage(pattern=r'/buscar\s+(.+)'))
async def cmd_buscar_text(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)

    sender = await event.get_sender()
    if sender:
        is_abusing, is_banned, abuse_msg = verificar_abuso(sender.id)
        if is_banned or is_abusing:
            await event.reply(abuse_msg, parse_mode='md')
            if is_abusing:
                await notificar_abuso(sender.id, f"{sender.first_name}", "Flood de /buscar")
            scan_paused = False
            return

    query = event.pattern_match.group(1).strip()
    await _executar_busca(event, query)
    scan_paused = False

async def _executar_busca(event, query: str):
    """Executa busca no banco + fallback API."""
    results = buscar_usuario(query)

    if not results:
        # Fallback: consulta via API do Telegram
        await responder_evento(event, f"🔍 `{query}` não encontrado no banco.\n\n🌐 **Consultando API do Telegram...**\n⏳ _Aguarde, mantendo status ativo..._")

        api_result = await consultar_api_telegram(query, event)
        _parar_digitando(event.chat_id)

        if api_result:
            results = [api_result]
            fonte = "\n\n🌐 _Resultado obtido via API Telegram e salvo no banco._"
        else:
            await responder_evento(
                event,
                f"❌ **Nenhum usuário encontrado para** `{query}`\n\n"
                f"💡 Tente buscar por ID numérico, @username ou parte do nome.\n"
                f"🌐 _API Telegram também não encontrou resultados._",
                buttons=voltar_button()
            )
            return
    else:
        fonte = ""

    if len(results) == 1:
        text = formatar_perfil(results[0]) + fonte
        await responder_evento(event, text, buttons=[
            [Button.inline("📜 Histórico Completo", f"hist_{results[0]['id']}_0".encode()),
             Button.inline("📂 Ver Grupos", f"ugroups_{results[0]['id']}_0".encode())],
            [Button.inline("🌐 Consultar API", f"apicheck_{results[0]['id']}".encode())],
            [Button.inline("🔙 Menu Principal", b"cmd_menu")]
        ])
    else:
        await mostrar_resultados_busca(event, query, results, 0)

async def mostrar_resultados_busca(event_or_msg, query, results, page):
    """Mostra resultados de busca com paginação de 10 itens."""
    total = len(results)
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = min(page, total_pages - 1)
    start = page * ITEMS_PER_PAGE
    chunk = results[start:start + ITEMS_PER_PAGE]

    text = f"🔍 **{total} resultados para** `{query}` (pág. {page + 1}/{total_pages}):\n\n"
    btns = []
    for r in chunk:
        label = f"👤 {r['nome_atual']} | {r['username_atual']}"
        btns.append([Button.inline(label[:40], f"profile_{r['id']}".encode())])

    # Navegação
    nav = []
    if page > 0:
        nav.append(Button.inline("◀️ Anterior", f"search_{page - 1}".encode()))
    if page < total_pages - 1:
        nav.append(Button.inline("Próxima ▶️", f"search_{page + 1}".encode()))
    if nav:
        btns.append(nav)
    btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])

    if hasattr(event_or_msg, 'reply'):
        await event_or_msg.reply(text, parse_mode='md', buttons=btns)
    else:
        await event_or_msg.edit(text, parse_mode='md', buttons=btns)

# ══════════════════════════════════════════════
# 📌  HANDLER: @InforUser_Bot + termo (GRUPOS)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=rf'(?i)@{BOT_USERNAME}\s+(.+)'))
async def cmd_mention_search(event):
    """Busca quando alguém usa @InforUser_Bot + termo."""
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)

    sender = await event.get_sender()
    if sender:
        is_abusing, is_banned, abuse_msg = verificar_abuso(sender.id)
        if is_banned or is_abusing:
            await event.reply(abuse_msg, parse_mode='md')
            if is_abusing:
                await notificar_abuso(sender.id, f"{sender.first_name}", f"Flood via @{BOT_USERNAME}")
            scan_paused = False
            return

    query = event.pattern_match.group(1).strip()
    await _executar_busca(event, query)
    scan_paused = False

# ══════════════════════════════════════════════
# 📋  HANDLER: REGRAS DO GRUPO
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'(?i)/regras?'))
async def cmd_regras(event):
    """Mostra as regras do grupo (descrição)."""
    if event.is_private:
        await event.reply("ℹ️ Este comando só funciona em grupos.", parse_mode='md')
        return

    await registrar_interacao(event)

    # Verifica se bot é admin
    is_bot_admin = await verificar_admin_bot(event.chat_id)
    if not is_bot_admin:
        await responder_evento(event, "⚠️ Preciso ser **administrador** para mostrar as regras.")
        return

    regras = await obter_regras_grupo(event.chat_id)

    await responder_evento(
        event,
        f"""╔══════════════════════════╗
║  📋 **REGRAS DO GRUPO**    ║
╚══════════════════════════╝

{regras}

━━━━━━━━━━━━━━━━━━━━━
_Use /regras a qualquer momento_
_Bot: @{BOT_USERNAME}_"""
    )

# ══════════════════════════════════════════════
# 👋  HANDLER: SAUDAÇÃO DE NOVOS MEMBROS
# ══════════════════════════════════════════════

@bot.on(events.ChatAction)
async def welcome_handler(event):
    """Sauda novos membros quando entram no grupo."""
    if not (event.user_joined or event.user_added):
        return

    try:
        chat_id = event.chat_id

        # Verifica se bot é admin
        is_bot_admin = await verificar_admin_bot(chat_id)
        if not is_bot_admin:
            return

        cfg = carregar_config()
        user = await event.get_user()
        if not user or user.bot:
            return

        nome = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Novo membro"
        mention = f"[{nome}](tg://user?id={user.id})"

        # Mensagem personalizada ou padrão
        msg_template = cfg.get("welcome_msgs", {}).get(str(chat_id))
        if msg_template:
            welcome_text = msg_template.replace("{nome}", nome).replace("{mention}", mention).replace("{grupo}", event.chat.title or "Grupo")
        else:
            welcome_text = f"""👋 **Bem-vindo(a), {mention}!**

Seja bem-vindo(a) ao grupo! 🎉

📋 Use /regras para ver as regras do grupo.
ℹ️ Use @{BOT_USERNAME} para consultas.

_Aproveite sua estadia!_ ✨"""

        # Registra no banco
        uid = str(user.id)
        db = carregar_dados()
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        phone = getattr(user, 'phone', None)
        phone_str = f"+{phone}" if phone else None

        if uid not in db:
            entry = {
                "id": user.id,
                "nome_atual": nome,
                "username_atual": f"@{user.username}" if user.username else "Nenhum",
                "grupos": [event.chat.title or "Grupo"],
                "primeiro_registro": agora,
                "historico": [],
                "origem": "entrada_grupo"
            }
            if phone_str:
                entry["telefone"] = phone_str
            db[uid] = entry
            salvar_dados(db)

        # Responde no tópico correto
        topic_id = cfg.get("topics", {}).get(str(chat_id))
        kwargs = {"parse_mode": "md"}
        if topic_id:
            kwargs["reply_to"] = topic_id
        await event.reply(welcome_text, **kwargs)

    except Exception as e:
        log(f"⚠️ Erro no welcome: {e}")

# ══════════════════════════════════════════════
# 🔘  HANDLERS DE CALLBACK (BOTÕES INLINE)
# ══════════════════════════════════════════════

search_pending = {}
last_search_results = {}
topic_pending = {}       # {chat_id: True} — aguardando ID do tópico
welcome_pending = {}     # {chat_id: True} — aguardando mensagem de saudação

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    global scan_paused
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    # Pausa a varredura durante interação com o bot
    scan_paused = True

    try:
        # Verificar abuso
        is_abusing, is_banned, abuse_msg = verificar_abuso(sender_id)
        if is_banned:
            await event.answer(abuse_msg[:200], alert=True)
            scan_paused = False
            return
        if is_abusing:
            await event.answer("⚠️ Muitos cliques! Aguarde.", alert=True)
            await notificar_abuso(sender_id, f"ID:{sender_id}", "Flood de botões")
            scan_paused = False
            return

        message = await event.get_message()

        # ── Menu Principal ──
        if data == "cmd_menu":
            await message.edit(
                f"""╔══════════════════════════════╗
║  🕵️ **User Info Bot Pro v{BOT_VERSION}**  ║
╚══════════════════════════════╝

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Buscar ──
        elif data == "cmd_buscar":
            search_pending[chat_id] = True
            await message.edit(
                f"""🔍 **Modo de Busca Ativo**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie** um dos seguintes:

• 🔢 **ID numérico** — ex: `123456789`
• 🆔 **@username** — ex: `@exemplo`
• 📛 **Nome** (parcial) — ex: `João`
• 📱 **Telefone** — ex: `+55119999`

━━━━━━━━━━━━━━━━━━━━━
💡 Ou use `@{BOT_USERNAME} termo` em qualquer chat!
_Aguardando sua busca..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Estatísticas ──
        elif data == "cmd_stats":
            db = carregar_dados()
            total_users = len([k for k in db if not k.startswith("_")])
            total_changes = sum(len(d.get("historico", [])) for k, d in db.items() if not k.startswith("_"))
            total_names = sum(1 for k, d in db.items() if not k.startswith("_") for h in d.get("historico", []) if h["tipo"] == "NOME")
            total_usernames = sum(1 for k, d in db.items() if not k.startswith("_") for h in d.get("historico", []) if h["tipo"] == "USER")

            with_history = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("historico"))
            with_phone = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("telefone"))
            from_api = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("origem") == "api_telegram")
            groups = set()
            for k, d in db.items():
                if not k.startswith("_"):
                    groups.update(d.get("grupos", []))

            last = scan_stats.get("last_scan", "Nunca")
            meta = db.get("_meta", {})
            total_scans = meta.get("total_varreduras", 0)

            # Abusos
            cfg = carregar_config()
            total_banned = len(cfg.get("banned_users", {}))
            total_warned = sum(v for v in cfg.get("abuse_warnings", {}).values())

            await message.edit(
                f"""╔══════════════════════════╗
║  📊 **ESTATÍSTICAS**       ║
╚══════════════════════════╝

👥 **Banco de Dados:**
├ 📋 Total de usuários: **{total_users}**
├ 📂 Grupos monitorados: **{len(groups)}**
├ 🔔 Usuários com alterações: **{with_history}**
├ 📱 Com telefone: **{with_phone}**
├ 🌐 Obtidos via API: **{from_api}**
└ 📊 Cobertura: **{(with_history/total_users*100) if total_users else 0:.1f}%**

📝 **Alterações Registradas:**
├ 📛 Mudanças de nome: **{total_names}**
├ 🆔 Mudanças de username: **{total_usernames}**
└ 📊 Total: **{total_changes}**

🛡️ **Segurança:**
├ 🚫 Usuários banidos: **{total_banned}**
└ ⚠️ Avisos emitidos: **{total_warned}**

⚙️ **Sistema:**
├ 🕐 Última varredura: `{last}`
├ 🔄 Total de varreduras: **{total_scans}**
├ 🔄 Intervalo: `{SCAN_INTERVAL // 60} min`
├ 📄 Itens/página: **{ITEMS_PER_PAGE}**
└ 💾 Tamanho do banco: **{os.path.getsize(FILE_PATH) // 1024 if os.path.exists(FILE_PATH) else 0} KB**

_Créditos: {OWNER_USER}_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Iniciar Varredura (ADMIN ONLY) ──
        elif data == "cmd_scan":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador pode iniciar varreduras.", alert=True)
                scan_paused = False
                return
            if scan_running:
                await event.answer("⏳ Varredura já em andamento!", alert=True)
            else:
                await event.answer("🔄 Varredura rápida iniciada!")
                scan_paused = False
                asyncio.create_task(executar_varredura(notify_chat=chat_id))
                return

        # ── Últimas Alterações (paginação 10 itens) ──
        elif data == "cmd_recent" or data.startswith("recent_page_"):
            page = 0
            if data.startswith("recent_page_"):
                page = int(data.split("_")[-1])

            db = carregar_dados()
            all_changes = []
            for uid, dados in db.items():
                if uid.startswith("_"):
                    continue
                for h in dados.get("historico", []):
                    all_changes.append({
                        **h,
                        "uid": uid,
                        "nome": dados["nome_atual"]
                    })

            all_changes.sort(key=lambda x: x["data"], reverse=True)
            total = len(all_changes)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            page = min(page, total_pages - 1)
            start = page * ITEMS_PER_PAGE
            chunk = all_changes[start:start + ITEMS_PER_PAGE]

            if not chunk:
                text = "📋 **Nenhuma alteração registrada ainda.**\n\nInicie uma varredura para detectar mudanças."
            else:
                text = f"📋 **Últimas Alterações** (pág. {page + 1}/{total_pages} — {total} total)\n\n"
                for c in chunk:
                    emoji = "📛" if c["tipo"] == "NOME" else "🆔"
                    text += f"{emoji} `{c['data']}`\n"
                    text += f"   👤 {c['nome']} — {c['de']} ➜ {c['para']}\n\n"

            await message.edit(text, parse_mode='md', buttons=paginar_buttons("recent", page, total_pages))

        # ── Exportar (ADMIN ONLY) ──
        elif data == "cmd_export":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador pode exportar o banco.", alert=True)
                scan_paused = False
                return
            if os.path.exists(FILE_PATH):
                await bot.send_file(
                    chat_id, FILE_PATH,
                    caption=f"📤 **Banco de dados exportado com sucesso!**\n\n_Créditos: {OWNER_USER}_",
                    parse_mode='md'
                )
                await event.answer("✅ Arquivo enviado!")
            else:
                await event.answer("❌ Banco vazio!", alert=True)

        # ── Configurações ──
        elif data == "cmd_config":
            cfg = carregar_config()
            topics_count = len(cfg.get("topics", {}))
            welcome_count = len(cfg.get("welcome_msgs", {}))
            banned_count = len(cfg.get("banned_users", {}))

            await message.edit(
                f"""⚙️ **Configurações Atuais**

━━━━━━━━━━━━━━━━━━━━━
🔄 Intervalo de varredura: **{SCAN_INTERVAL // 60} min**
📜 Máx. histórico/usuário: **{MAX_HISTORY}**
📄 Itens por página: **{ITEMS_PER_PAGE}**
⚡ Batch de varredura: **{SCAN_BATCH_SIZE}**
⏱️ Delay entre lotes: **{SCAN_BATCH_DELAY}s**
💾 Banco: `{FILE_PATH}`
📝 Logs: `{LOG_PATH}`
━━━━━━━━━━━━━━━━━━━━━

📌 **Tópicos configurados:** {topics_count}
👋 **Saudações personalizadas:** {welcome_count}
🚫 **Usuários banidos:** {banned_count}

🔧 **Recursos v{BOT_VERSION}:**
• ⚡ Varredura otimizada em lotes
• 🔒 Pausa automática durante uso
• 📂 Rastreamento de grupos
• 📄 Paginação completa (10/pág)
• 🆕 Criação automática do banco
• 📌 Suporte a tópicos (topics)
• 👋 Saudação de novos membros
• 🌐 Consulta API Telegram (fallback)
• 📱 Captura de telefone
• 🛡️ Controle de abuso
• 📣 Notificações em grupos (admin)
• 📋 Exibição de regras do grupo

_Para alterar, edite as constantes no código._
_Créditos: {OWNER_USER}_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Configurar Tópico ──
        elif data == "cmd_set_topic":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas admin.", alert=True)
                scan_paused = False
                return
            topic_pending[chat_id] = True
            await message.edit(
                """📌 **Configurar Tópico**

━━━━━━━━━━━━━━━━━━━━━
Envie o **ID do chat** e **ID do tópico** no formato:

`chat_id:topic_id`

Exemplo: `-1001234567890:12345`

💡 Para remover, envie: `chat_id:0`
━━━━━━━━━━━━━━━━━━━━━
_Aguardando..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Configurar Saudação ──
        elif data == "cmd_set_welcome":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas admin.", alert=True)
                scan_paused = False
                return
            welcome_pending[chat_id] = True
            await message.edit(
                f"""👋 **Configurar Saudação**

━━━━━━━━━━━━━━━━━━━━━
Envie no formato:

`chat_id|mensagem`

**Variáveis disponíveis:**
• `{{nome}}` — Nome do membro
• `{{mention}}` — Menção clicável
• `{{grupo}}` — Nome do grupo

**Exemplo:**
`-1001234567890|Olá {{mention}}! Bem-vindo(a) ao {{grupo}}!`

💡 Para remover: `chat_id|`
━━━━━━━━━━━━━━━━━━━━━""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Painel de Abuso ──
        elif data == "cmd_abuse_panel":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas admin.", alert=True)
                scan_paused = False
                return

            cfg = carregar_config()
            banned = cfg.get("banned_users", {})
            warnings = cfg.get("abuse_warnings", {})

            text = f"""🛡️ **Painel de Controle de Abuso**

━━━━━━━━━━━━━━━━━━━━━
📊 **Configuração:**
├ ⚡ Máx. comandos/janela: **{ABUSE_MAX_COMMANDS}**
├ ⏱️ Janela: **{ABUSE_WINDOW}s**
├ ⚠️ Avisos até ban: **{ABUSE_WARN_THRESHOLD}**
└ 🚫 Duração ban: **{ABUSE_BAN_DURATION // 60} min**

🚫 **Banidos atualmente:** {len(banned)}
"""
            if banned:
                for uid, info in list(banned.items())[:5]:
                    until = datetime.fromtimestamp(info["until"]).strftime("%d/%m %H:%M")
                    text += f"  • `{uid}` — até `{until}` — _{info.get('reason', 'N/A')}_\n"

            text += f"""
⚠️ **Com avisos:** {len(warnings)}
"""
            if warnings:
                for uid, count in list(warnings.items())[:5]:
                    text += f"  • `{uid}` — **{count}** aviso(s)\n"

            await message.edit(text, parse_mode='md', buttons=[
                [Button.inline("🔄 Resetar Avisos", b"abuse_reset_all"),
                 Button.inline("✅ Desbanir Todos", b"abuse_unban_all")],
                [Button.inline("🔙 Menu Principal", b"cmd_menu")]
            ])

        # ── Ações de Abuso ──
        elif data.startswith("abuse_warn_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            target_id = int(data.replace("abuse_warn_", ""))
            try:
                await bot.send_message(
                    target_id,
                    f"⚠️ **AVISO DO ADMINISTRADOR**\n\n"
                    f"Você está fazendo uso excessivo do bot.\n"
                    f"Continue e será **banido temporariamente**.\n\n"
                    f"_Administrador: {OWNER_USER}_",
                    parse_mode='md'
                )
                await event.answer("✅ Aviso enviado!", alert=True)
            except Exception as e:
                await event.answer(f"❌ Erro: {e}", alert=True)

        elif data.startswith("abuse_ban_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            parts = data.split("_")
            target_id = parts[2]
            duration = int(parts[3]) if len(parts) > 3 else 3600
            cfg = carregar_config()
            if "banned_users" not in cfg:
                cfg["banned_users"] = {}
            cfg["banned_users"][target_id] = {
                "until": time.time() + duration,
                "reason": f"Ban manual pelo admin ({duration // 60} min)",
                "banned_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            salvar_config(cfg)
            try:
                await bot.send_message(
                    int(target_id),
                    f"🚫 **Você foi BANIDO** do bot por **{duration // 60} minutos**.\n\n"
                    f"Motivo: Uso excessivo / Abuso\n"
                    f"_Administrador: {OWNER_USER}_",
                    parse_mode='md'
                )
            except Exception:
                pass
            await event.answer(f"🚫 Usuário banido por {duration // 60} min!", alert=True)

        elif data.startswith("abuse_unban_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            target_id = data.replace("abuse_unban_", "")
            cfg = carregar_config()
            if target_id in cfg.get("banned_users", {}):
                del cfg["banned_users"][target_id]
                salvar_config(cfg)
                await event.answer("✅ Usuário desbanido!", alert=True)
            else:
                await event.answer("ℹ️ Usuário não está banido.", alert=True)

        elif data == "abuse_reset_all":
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            cfg = carregar_config()
            cfg["abuse_warnings"] = {}
            salvar_config(cfg)
            abuse_tracker.clear()
            await event.answer("✅ Todos os avisos resetados!", alert=True)

        elif data == "abuse_unban_all":
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            cfg = carregar_config()
            cfg["banned_users"] = {}
            salvar_config(cfg)
            await event.answer("✅ Todos desbanidos!", alert=True)

        elif data.startswith("abuse_log_"):
            target_id = data.replace("abuse_log_", "")
            db = carregar_dados()
            if target_id in db:
                dados = db[target_id]
                text = f"📋 **Interações de** `{dados['nome_atual']}`\n"
                text += f"🔢 ID: `{target_id}`\n"
                text += f"🆔 Username: `{dados.get('username_atual', 'N/A')}`\n"
                text += f"📱 Telefone: `{dados.get('telefone', 'N/A')}`\n"
                text += f"📅 Primeiro registro: `{dados.get('primeiro_registro', 'N/A')}`\n"
                text += f"🏷️ Origem: `{dados.get('origem', 'N/A')}`\n\n"

                historico = dados.get("historico", [])[-10:]
                if historico:
                    text += "📜 **Últimas alterações:**\n"
                    for h in reversed(historico):
                        emoji = "📛" if h.get("tipo") == "NOME" else "🆔"
                        text += f"  {emoji} `{h['data']}` — {h['de']} ➜ {h['para']}\n"
                else:
                    text += "_Sem alterações registradas._\n"

                await message.edit(text, parse_mode='md', buttons=[
                    [Button.inline("⚠️ Enviar Aviso", f"abuse_warn_{target_id}".encode()),
                     Button.inline("🚫 Banir", f"abuse_ban_{target_id}_3600".encode())],
                    [Button.inline("🔙 Menu", b"cmd_menu")]
                ])
            else:
                await event.answer("❌ Usuário não encontrado no banco.", alert=True)

        # ── Consultar API (botão) ──
        elif data.startswith("apicheck_"):
            uid = data.replace("apicheck_", "")
            await event.answer("🌐 Consultando API Telegram...")
            result = await consultar_api_telegram(uid, event=None)
            _parar_digitando(chat_id)
            if result:
                await message.edit(
                    formatar_perfil(result) + "\n\n🌐 _Dados atualizados via API Telegram._",
                    parse_mode='md',
                    buttons=[
                        [Button.inline("📜 Histórico", f"hist_{uid}_0".encode()),
                         Button.inline("📂 Grupos", f"ugroups_{uid}_0".encode())],
                        [Button.inline("🔙 Menu", b"cmd_menu")]
                    ]
                )
            else:
                await event.answer("❌ API não retornou dados.", alert=True)

        # ── Grupos do Usuário (buscar) ──
        elif data == "cmd_grupos":
            search_pending[chat_id] = "grupos"
            await message.edit(
                """📂 **Buscar Grupos de um Usuário**

━━━━━━━━━━━━━━━━━━━━━
📝 Envie o **ID**, **@username** ou **nome** do usuário para ver em quais grupos ele está.

━━━━━━━━━━━━━━━━━━━━━
_Aguardando..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Limpar Cache ──
        elif data == "cmd_clear_cache":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                scan_paused = False
                return
            last_search_results.clear()
            search_pending.clear()
            topic_pending.clear()
            welcome_pending.clear()
            await event.answer("✅ Cache limpo!", alert=True)

        # ── Sobre ──
        elif data == "cmd_about":
            await message.edit(
                f"""╔══════════════════════════════╗
║  ℹ️ **SOBRE O BOT**           ║
╚══════════════════════════════╝

🕵️ **User Info Bot Pro v{BOT_VERSION}**
_Monitor profissional de usuários_

━━━━━━━━━━━━━━━━━━━━━
**Funcionalidades:**
• 🔍 Busca por ID, @user, nome ou telefone
• 📡 Varredura rápida otimizada
• 🔔 Notificações de alterações
• 📜 Histórico paginado (10/pág)
• 📂 Rastreamento de grupos
• 📤 Exportação de dados
• 📊 Estatísticas detalhadas
• 🔒 Pausa durante interações
• 🆕 Auto-criação do banco
• 📌 Suporte a tópicos (topics)
• 👋 Saudação de novos membros
• 🌐 Consulta API Telegram (fallback)
• 📱 Captura de telefone
• 🛡️ Controle de abuso (warn/ban)
• 📋 Exibição de regras do grupo
• 📣 Notificações em grupos (admin)
• 🔄 @{BOT_USERNAME} + termo

**Tecnologia:**
• ⚡ Telethon (asyncio)
• 💾 Banco JSON local
• 🛡️ Anti-flood integrado
• 🔄 Lock de operações
• 🌐 API Telegram fallback

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 **Criado por:** {OWNER_NAME}
📱 **Contato:** {OWNER_USER}
🔖 **Versão:** {BOT_VERSION} ({BOT_CODENAME})
━━━━━━━━━━━━━━━━━━━━━""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Perfil individual ──
        elif data.startswith("profile_"):
            uid = data.replace("profile_", "")
            db = carregar_dados()
            if uid in db:
                await message.edit(formatar_perfil(db[uid]), parse_mode='md', buttons=[
                    [Button.inline("📜 Histórico Completo", f"hist_{uid}_0".encode()),
                     Button.inline("📂 Ver Grupos", f"ugroups_{uid}_0".encode())],
                    [Button.inline("🌐 Consultar API", f"apicheck_{uid}".encode())],
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ])
            else:
                await event.answer("❌ Usuário não encontrado no banco.")

        # ── Grupos de um usuário (paginado) ──
        elif data.startswith("ugroups_"):
            parts = data.split("_")
            uid = parts[1]
            page = int(parts[2]) if len(parts) > 2 else 0

            db = carregar_dados()
            if uid not in db:
                await event.answer("❌ Usuário não encontrado.")
                scan_paused = False
                return

            dados = db[uid]
            grupos = dados.get("grupos", [])
            total = len(grupos)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            page = min(page, total_pages - 1)
            start = page * ITEMS_PER_PAGE
            chunk = grupos[start:start + ITEMS_PER_PAGE]

            text = f"📂 **Grupos de** `{dados['nome_atual']}`\n"
            text += f"🔢 ID: `{uid}` — Página {page + 1}/{total_pages}\n"
            text += f"📊 Total: **{total}** grupos\n\n"

            if chunk:
                for i, g in enumerate(chunk, start + 1):
                    text += f"  {i}. 📁 {g}\n"
            else:
                text += "_Nenhum grupo registrado._"

            btns = paginar_buttons(f"ugroups_{uid}", page, total_pages)
            await message.edit(text, parse_mode='md', buttons=btns)

        # ── Histórico paginado de um usuário (10 por página) ──
        elif data.startswith("hist_"):
            parts = data.split("_")
            uid = parts[1]
            page = int(parts[2]) if len(parts) > 2 else 0

            db = carregar_dados()
            if uid not in db:
                await event.answer("❌ Usuário não encontrado.")
                scan_paused = False
                return

            dados = db[uid]
            historico = list(reversed(dados.get("historico", [])))
            total = len(historico)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            page = min(page, total_pages - 1)
            start = page * ITEMS_PER_PAGE
            chunk = historico[start:start + ITEMS_PER_PAGE]

            text = f"📜 **Histórico de** `{dados['nome_atual']}`\n"
            text += f"🔢 ID: `{uid}` — Página {page + 1}/{total_pages}\n"
            text += f"📊 Total: **{total}** alterações\n\n"

            for h in chunk:
                emoji = "📛" if h.get("tipo") == "NOME" else "🆔"
                grupo = h.get("grupo", "N/A")
                text += f"{emoji} `{h['data']}`\n"
                text += f"   {h['de']} ➜ {h['para']}\n"
                text += f"   📍 _{grupo}_\n\n"

            if not chunk:
                text += "_Nenhum registro._"

            btns = paginar_buttons(f"hist_{uid}", page, total_pages)
            await message.edit(text, parse_mode='md', buttons=btns)

        # ── Noop (indicador de página) ──
        elif data == "noop":
            await event.answer()

        else:
            await event.answer("⚠️ Ação não reconhecida.")

        try:
            await event.answer()
        except:
            pass

    except Exception as e:
        log(f"❌ Callback error: {e}")
        try:
            await event.answer("❌ Erro interno.")
        except:
            pass
    finally:
        scan_paused = False  # Sempre retoma a varredura

# ══════════════════════════════════════════════
# 💬  HANDLER: TEXTO LIVRE (BUSCA + CONFIG)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and not re.match(rf'(?i)@{BOT_USERNAME}\s+', e.text)))
async def text_handler(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)
    chat_id = event.chat_id
    sender_id = event.sender_id

    # Verificar abuso
    sender = await event.get_sender()
    if sender:
        is_abusing, is_banned, abuse_msg = verificar_abuso(sender.id)
        if is_banned:
            await event.reply(abuse_msg, parse_mode='md')
            scan_paused = False
            return
        if is_abusing:
            await event.reply(abuse_msg, parse_mode='md')
            await notificar_abuso(sender.id, f"{sender.first_name}", "Flood de mensagens")
            scan_paused = False
            return

    # ── Configuração de Tópico ──
    if chat_id in topic_pending and is_admin(sender_id):
        topic_pending.pop(chat_id)
        text = event.text.strip()
        if ":" in text:
            parts = text.split(":")
            try:
                target_chat = int(parts[0].strip())
                topic_id = int(parts[1].strip())
                cfg = carregar_config()
                if "topics" not in cfg:
                    cfg["topics"] = {}
                if topic_id == 0:
                    cfg["topics"].pop(str(target_chat), None)
                    salvar_config(cfg)
                    await event.reply(f"✅ Tópico removido para `{target_chat}`", parse_mode='md', buttons=voltar_button())
                else:
                    cfg["topics"][str(target_chat)] = topic_id
                    salvar_config(cfg)
                    await event.reply(f"✅ Tópico `{topic_id}` configurado para `{target_chat}`", parse_mode='md', buttons=voltar_button())
            except ValueError:
                await event.reply("❌ Formato inválido. Use: `chat_id:topic_id`", parse_mode='md', buttons=voltar_button())
        else:
            await event.reply("❌ Formato inválido. Use: `chat_id:topic_id`", parse_mode='md', buttons=voltar_button())
        scan_paused = False
        return

    # ── Configuração de Saudação ──
    if chat_id in welcome_pending and is_admin(sender_id):
        welcome_pending.pop(chat_id)
        text = event.text.strip()
        if "|" in text:
            parts = text.split("|", 1)
            try:
                target_chat = int(parts[0].strip())
                msg = parts[1].strip()
                cfg = carregar_config()
                if "welcome_msgs" not in cfg:
                    cfg["welcome_msgs"] = {}
                if not msg:
                    cfg["welcome_msgs"].pop(str(target_chat), None)
                    salvar_config(cfg)
                    await event.reply(f"✅ Saudação removida para `{target_chat}`", parse_mode='md', buttons=voltar_button())
                else:
                    cfg["welcome_msgs"][str(target_chat)] = msg
                    salvar_config(cfg)
                    await event.reply(f"✅ Saudação configurada para `{target_chat}`:\n\n_{msg}_", parse_mode='md', buttons=voltar_button())
            except ValueError:
                await event.reply("❌ Formato inválido. Use: `chat_id|mensagem`", parse_mode='md', buttons=voltar_button())
        else:
            await event.reply("❌ Formato inválido. Use: `chat_id|mensagem`", parse_mode='md', buttons=voltar_button())
        scan_paused = False
        return

    # ── Busca pendente ──
    if chat_id in search_pending:
        mode = search_pending.pop(chat_id)
        query = event.text.strip()
        results = buscar_usuario(query)

        if not results:
            # Fallback API
            await event.reply(
                f"🔍 `{query}` não encontrado no banco.\n🌐 **Consultando API Telegram...**",
                parse_mode='md'
            )
            api_result = await consultar_api_telegram(query, event)
            _parar_digitando(event.chat_id)

            if api_result:
                results = [api_result]
            else:
                await event.reply(
                    f"❌ **Nenhum resultado para** `{query}`\n\n💡 Tente outro termo.\n🌐 _API também não encontrou._",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                scan_paused = False
                return

        # Se é busca de grupos
        if mode == "grupos":
            if len(results) == 1:
                dados = results[0]
                uid = str(dados["id"])
                grupos = dados.get("grupos", [])
                text = f"📂 **Grupos de** `{dados['nome_atual']}`\n"
                text += f"🔢 ID: `{uid}`\n"
                text += f"📊 Total: **{len(grupos)}** grupos\n\n"
                for i, g in enumerate(grupos[:ITEMS_PER_PAGE], 1):
                    text += f"  {i}. 📁 {g}\n"
                if len(grupos) > ITEMS_PER_PAGE:
                    text += f"\n_... e mais {len(grupos) - ITEMS_PER_PAGE} grupos_"

                btns = []
                if len(grupos) > ITEMS_PER_PAGE:
                    btns.append([Button.inline("📂 Ver Todos", f"ugroups_{uid}_0".encode())])
                btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])
                await event.reply(text, parse_mode='md', buttons=btns)
            else:
                text = f"🔍 **{len(results)} resultados** — selecione:\n\n"
                btns = []
                for r in results[:ITEMS_PER_PAGE]:
                    label = f"📂 {r['nome_atual']} ({len(r.get('grupos', []))} grupos)"
                    btns.append([Button.inline(label[:40], f"ugroups_{r['id']}_0".encode())])
                btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])
                await event.reply(text, parse_mode='md', buttons=btns)
        else:
            # Busca normal
            if len(results) == 1:
                await event.reply(formatar_perfil(results[0]), parse_mode='md', buttons=[
                    [Button.inline("📜 Histórico Completo", f"hist_{results[0]['id']}_0".encode()),
                     Button.inline("📂 Ver Grupos", f"ugroups_{results[0]['id']}_0".encode())],
                    [Button.inline("🌐 Consultar API", f"apicheck_{results[0]['id']}".encode())],
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ])
            else:
                # Salva resultados para paginação
                last_search_results[chat_id] = {"query": query, "results": results}
                await mostrar_resultados_busca(event, query, results, 0)
    else:
        # Apenas em privado dá dica
        if event.is_private:
            await event.reply(
                f"💡 Use o menu para navegar ou `/buscar termo` para buscar.\n"
                f"💡 Em grupos: `@{BOT_USERNAME} termo`",
                parse_mode='md',
                buttons=menu_principal_buttons(event.sender_id)
            )
    scan_paused = False

# ══════════════════════════════════════════════
# 🔁  VARREDURA AUTOMÁTICA
# ══════════════════════════════════════════════

async def auto_scanner():
    """Executa varreduras periódicas automaticamente."""
    while True:
        await asyncio.sleep(SCAN_INTERVAL)
        if not scan_running:
            log("🔄 Varredura automática iniciada")
            await executar_varredura()

# ══════════════════════════════════════════════
# 🚀  MAIN
# ══════════════════════════════════════════════

async def main():
    await user_client.start(PHONE)
    await bot.start(bot_token=BOT_TOKEN)

    me = await bot.get_me()
    log(f"🤖 Bot: @{me.username} (ID: {me.id})")
    log(f"🚀 User Info Bot Pro v{BOT_VERSION} ({BOT_CODENAME}) iniciado!")
    log(f"👨‍💻 Créditos: {OWNER_NAME} {OWNER_USER}")

    # Criação automática do banco na primeira execução
    primeiro_inicio = inicializar_banco()
    if primeiro_inicio:
        log("🆕 Primeira execução — banco criado automaticamente")
        await notificar(
            f"🆕 **Primeira Execução!**\n\n"
            f"✅ Banco de dados criado automaticamente.\n"
            f"📡 Iniciando varredura inicial...\n\n"
            f"_O bot estará operacional em instantes._"
        )

    log(f"🔄 Varredura automática a cada {SCAN_INTERVAL // 60} min")
    log(f"📄 Paginação: {ITEMS_PER_PAGE} itens por página")
    log(f"🛡️ Controle de abuso: {ABUSE_MAX_COMMANDS} cmds/{ABUSE_WINDOW}s")
    log(f"📌 Suporte a tópicos: ATIVADO")
    log(f"👋 Saudação de membros: ATIVADO")
    log(f"🌐 API Telegram fallback: ATIVADO")
    log("📡 Executando primeira varredura...")

    # Primeira varredura ao iniciar
    await executar_varredura(notify_chat=OWNER_ID)

    # Agenda varreduras automáticas
    asyncio.create_task(auto_scanner())

    print(f"✅ Bot ativo! Use /start, /buscar ou @{BOT_USERNAME} termo")
    await asyncio.gather(
        bot.run_until_disconnected(),
        user_client.run_until_disconnected()
    )

if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
