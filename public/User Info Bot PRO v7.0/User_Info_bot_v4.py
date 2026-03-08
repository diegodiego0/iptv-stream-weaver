import json
import os
import asyncio
import time
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, UserNotParticipantError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest, GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest, ExportChatInviteRequest
from telethon.tl.types import (
    ChannelParticipantAdmin, ChannelParticipantCreator,
    InputPeerUser, PeerChannel, PeerChat,
    ChatInviteExported
)

# ══════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES
# ══════════════════════════════════════════════
API_ID = 29214781                        # Obtenha em https://my.telegram.org
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102                 # Edivaldo Silva @Edkd1
BOT_USERNAME = "InforUser_Bot"        # Username do bot (sem @)

FOLDER_PATH = "data"
FILE_PATH = os.path.join(FOLDER_PATH, "user_database.json")
LOG_PATH = os.path.join(FOLDER_PATH, "monitor.log")
CONFIG_PATH = os.path.join(FOLDER_PATH, "bot_config.json")
GROUPS_FILE_PATH = os.path.join(FOLDER_PATH, "groups_bot.json")
SESSION_USER = "session_monitor"
SESSION_BOT = "session_bot"

ITEMS_PER_PAGE = 10                   # 10 itens por página
SCAN_INTERVAL = 1800                  # Varredura a cada 30 min (mais rápido)
MAX_HISTORY = 50
SCAN_BATCH_SIZE = 200                 # Participantes por lote para varredura rápida
SCAN_BATCH_DELAY = 0.3               # Delay entre lotes (menor = mais rápido)
FLOOD_WAIT_MARGIN = 1.2              # Multiplicador de segurança para FloodWait

# ── Controle de Abuso ──
ABUSE_MAX_COMMANDS = 10               # Máximo de comandos por janela
ABUSE_WINDOW = 60                     # Janela em segundos
ABUSE_WARN_THRESHOLD = 3             # Avisos antes de banir
ABUSE_BAN_DURATION = 3600            # Ban temporário (1 hora)

# ══════════════════════════════════════════════
# 📁  BANCO DE DADOS JSON — CRIAÇÃO AUTOMÁTICA
# ══════════════════════════════════════════════
os.makedirs(FOLDER_PATH, exist_ok=True)

def inicializar_banco():
    """Cria o banco de dados na primeira execução com estrutura padrão."""
    if not os.path.exists(FILE_PATH):
        estrutura_inicial = {
            "_meta": {
                "versao": "7.0",
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
            return {"_meta": {"versao": "7.0", "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}
    return {"_meta": {"versao": "7.0", "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}

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
# 📋  CONFIGURAÇÃO DINÂMICA (Tópicos, Boas-vindas)
# ══════════════════════════════════════════════

_config_cache = None
_config_cache_time = 0
_CONFIG_CACHE_TTL = 5  # Segundos de cache para resposta rápida

def carregar_config() -> dict:
    """Carrega configurações dinâmicas do bot com cache em memória."""
    global _config_cache, _config_cache_time
    agora = time.time()
    if _config_cache is not None and (agora - _config_cache_time) < _CONFIG_CACHE_TTL:
        return _config_cache
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                _config_cache = json.load(f)
                _config_cache_time = agora
                return _config_cache
        except (json.JSONDecodeError, IOError):
            pass
    _config_cache = {
        "topicos": {},
        "boas_vindas": {},
        "usuarios_banidos": {},
        "abuse_log": {}
    }
    _config_cache_time = agora
    return _config_cache

def salvar_config(cfg: dict):
    global _config_cache, _config_cache_time
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        _config_cache = cfg
        _config_cache_time = time.time()
    except IOError as e:
        log(f"❌ Erro ao salvar config: {e}")


# ══════════════════════════════════════════════
# 📂  REGISTRO DE GRUPOS DO BOT
# ══════════════════════════════════════════════

def carregar_grupos_bot() -> dict:
    """Carrega o arquivo de grupos onde o bot foi adicionado."""
    if os.path.exists(GROUPS_FILE_PATH):
        try:
            with open(GROUPS_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def salvar_grupos_bot(data: dict):
    try:
        with open(GROUPS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar grupos_bot: {e}")

async def registrar_grupo_bot(chat, adicionado_por=None):
    """Registra informações do grupo onde o bot foi adicionado."""
    try:
        grupos = carregar_grupos_bot()
        chat_id = str(chat.id)
        title = getattr(chat, 'title', 'Grupo desconhecido')
        username = getattr(chat, 'username', None)
        
        # Tenta obter link de acesso
        link = None
        if username:
            link = f"https://t.me/{username}"
        else:
            try:
                result = await bot(ExportChatInviteRequest(chat))
                if isinstance(result, ChatInviteExported):
                    link = result.link
            except Exception:
                pass

        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        if chat_id not in grupos:
            grupos[chat_id] = {
                "id": chat.id,
                "nome": title,
                "username": f"@{username}" if username else "Nenhum",
                "link": link or "Não disponível",
                "adicionado_em": agora,
                "adicionado_por": adicionado_por,
                "membros": getattr(chat, 'participants_count', None),
                "ativo": True
            }
            salvar_grupos_bot(grupos)
            log(f"📂 Novo grupo registrado: {title} ({chat_id})")
            
            # Notifica o dono
            por_txt = f"\n👤 **Adicionado por:** `{adicionado_por}`" if adicionado_por else ""
            await notificar(
                f"📂 **BOT ADICIONADO A GRUPO**\n\n"
                f"╔══════════════════════════╗\n"
                f"║  📋 **{title}**\n"
                f"╚══════════════════════════╝\n\n"
                f"🔢 **ID:** `{chat.id}`\n"
                f"🆔 **Username:** `{'@' + username if username else 'Nenhum'}`\n"
                f"🔗 **Link:** `{link or 'Não disponível'}`\n"
                f"👥 **Membros:** {getattr(chat, 'participants_count', '?')}"
                f"{por_txt}\n"
                f"🕐 **Data:** `{agora}`"
            )
        else:
            # Atualiza info
            grupos[chat_id]["nome"] = title
            grupos[chat_id]["username"] = f"@{username}" if username else "Nenhum"
            if link:
                grupos[chat_id]["link"] = link
            grupos[chat_id]["ativo"] = True
            salvar_grupos_bot(grupos)
    except Exception as e:
        log(f"⚠️ Erro ao registrar grupo: {e}")


async def is_group_owner(chat_id, user_id) -> bool:
    """Verifica se o user_id é o criador/dono do grupo."""
    try:
        participant = await bot(GetParticipantRequest(chat_id, user_id))
        return isinstance(participant.participant, ChannelParticipantCreator)
    except Exception:
        return False

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


def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID


# ══════════════════════════════════════════════
# 🛡️  SISTEMA DE CONTROLE DE ABUSO
# ══════════════════════════════════════════════

def verificar_abuso(user_id: int) -> dict:
    """
    Verifica se o usuário está abusando do bot.
    Retorna: {"permitido": bool, "motivo": str, "avisos": int}
    """
    cfg = carregar_config()
    uid = str(user_id)
    agora = time.time()

    # Verifica se está banido
    ban_info = cfg.get("usuarios_banidos", {}).get(uid)
    if ban_info:
        ban_ate = ban_info.get("ate", 0)
        if agora < ban_ate:
            restante = int(ban_ate - agora)
            mins = restante // 60
            return {
                "permitido": False,
                "motivo": f"🚫 Você está temporariamente banido.\n⏳ Tempo restante: **{mins} min {restante % 60}s**",
                "avisos": ban_info.get("avisos", 0)
            }
        else:
            # Ban expirou — remove
            del cfg["usuarios_banidos"][uid]
            salvar_config(cfg)

    # Verifica rate limiting
    if "abuse_log" not in cfg:
        cfg["abuse_log"] = {}
    
    if uid not in cfg["abuse_log"]:
        cfg["abuse_log"][uid] = []
    
    # Remove timestamps antigos
    cfg["abuse_log"][uid] = [t for t in cfg["abuse_log"][uid] if agora - t < ABUSE_WINDOW]
    cfg["abuse_log"][uid].append(agora)
    salvar_config(cfg)

    # Verifica se excedeu o limite
    if len(cfg["abuse_log"][uid]) > ABUSE_MAX_COMMANDS:
        avisos = cfg.get("usuarios_banidos", {}).get(uid, {}).get("avisos", 0) + 1
        
        if avisos >= ABUSE_WARN_THRESHOLD:
            # Aplica ban
            if "usuarios_banidos" not in cfg:
                cfg["usuarios_banidos"] = {}
            cfg["usuarios_banidos"][uid] = {
                "ate": agora + ABUSE_BAN_DURATION,
                "avisos": avisos,
                "banido_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            salvar_config(cfg)
            return {
                "permitido": False,
                "motivo": f"🚫 **BANIDO TEMPORARIAMENTE**\nVocê excedeu o limite de uso.\n⏳ Duração: **{ABUSE_BAN_DURATION // 60} minutos**",
                "avisos": avisos
            }
        else:
            # Apenas aviso
            if "usuarios_banidos" not in cfg:
                cfg["usuarios_banidos"] = {}
            cfg["usuarios_banidos"][uid] = {"ate": 0, "avisos": avisos}
            salvar_config(cfg)
            return {
                "permitido": False,
                "motivo": f"⚠️ **AVISO {avisos}/{ABUSE_WARN_THRESHOLD}**\nVocê está enviando comandos rápido demais.\nAguarde alguns segundos.",
                "avisos": avisos
            }

    return {"permitido": True, "motivo": "", "avisos": 0}


async def notificar_abuso(user_id: int, user_name: str, username: str, acao: str, avisos: int):
    """Envia notificação de abuso ao dono do bot via DM."""
    try:
        btns = [
            [Button.inline("⚠️ Enviar Aviso", f"abuse_warn_{user_id}".encode()),
             Button.inline("🚫 Banir 1h", f"abuse_ban_{user_id}_3600".encode())],
            [Button.inline("🚫 Banir 24h", f"abuse_ban_{user_id}_86400".encode()),
             Button.inline("✅ Desbloquear", f"abuse_unban_{user_id}".encode())],
            [Button.inline("📊 Ver Interações", f"abuse_log_{user_id}".encode())]
        ]
        await bot.send_message(
            OWNER_ID,
            f"""🚨 **ALERTA DE ABUSO**

╔══════════════════════════╗
║  ⚠️ USO EXCESSIVO         ║
╚══════════════════════════╝

👤 **Usuário:** `{user_name}`
🆔 **Username:** `{username}`
🔢 **ID:** `{user_id}`
📊 **Avisos:** {avisos}/{ABUSE_WARN_THRESHOLD}
📝 **Ação:** {acao}
🕐 **Horário:** `{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}`

_Selecione uma ação abaixo:_""",
            parse_mode='md',
            buttons=btns
        )
    except Exception as e:
        log(f"⚠️ Erro ao notificar abuso: {e}")


# ══════════════════════════════════════════════
# 🔍  CONSULTA VIA API DO TELEGRAM
# ══════════════════════════════════════════════

async def consultar_api_telegram(query: str, event=None) -> dict | None:
    """
    Consulta a API do Telegram quando o usuário não é encontrado no banco.
    Mantém status 'digitando' durante a consulta.
    Salva resultado no banco para consultas futuras.
    """
    try:
        # Mantém status digitando (cancelável)
        typing_task_id = None
        if event:
            chat_id = event.chat_id
            sender_id = getattr(event, 'sender_id', 0)
            typing_task_id = iniciar_digitando(chat_id, sender_id)

        entity = None
        # Tenta por ID numérico
        if query.isdigit():
            try:
                entity = await user_client.get_entity(int(query))
            except Exception:
                pass

        # Tenta por username
        if not entity and query.startswith("@"):
            try:
                entity = await user_client.get_entity(query)
            except Exception:
                pass

        # Tenta por username sem @
        if not entity and not query.isdigit():
            try:
                entity = await user_client.get_entity(f"@{query}")
            except Exception:
                pass

        if not entity:
            return None

        # Obtém informações completas
        try:
            full = await user_client(GetFullUserRequest(entity.id))
            bio = full.full_user.about or ""
        except Exception:
            bio = ""

        uid = str(entity.id)
        nome = f"{entity.first_name or ''} {entity.last_name or ''}".strip() or "Sem nome"
        username = f"@{entity.username}" if entity.username else "Nenhum"
        phone = entity.phone if hasattr(entity, 'phone') and entity.phone else None
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Salva no banco de dados
        db = carregar_dados()
        if uid not in db:
            db[uid] = {
                "id": entity.id,
                "nome_atual": nome,
                "username_atual": username,
                "grupos": [],
                "primeiro_registro": agora,
                "historico": [],
                "origem": "api_telegram",
                "bio": bio
            }
            if phone:
                db[uid]["telefone"] = phone
            salvar_dados(db)
            log(f"📡 Usuário salvo via API: {nome} ({uid})")
        else:
            # Atualiza bio e telefone se existente
            if bio:
                db[uid]["bio"] = bio
            if phone:
                db[uid]["telefone"] = phone
            salvar_dados(db)

        return db[uid]

    except Exception as e:
        log(f"⚠️ Erro na consulta API: {e}")
        return None


_typing_tasks = {}  # chat_id -> asyncio.Task para cancelar digitando

async def _manter_digitando(chat_id: int, task_id: str):
    """Mantém o status 'digitando' enquanto a consulta está em andamento. Cancelável."""
    try:
        for _ in range(30):
            async with bot.action(chat_id, 'typing'):
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        _typing_tasks.pop(task_id, None)


def iniciar_digitando(chat_id: int, sender_id: int):
    """Inicia indicador de digitando e retorna o task_id para cancelar depois."""
    task_id = f"{chat_id}_{sender_id}_{time.time()}"
    task = asyncio.create_task(_manter_digitando(chat_id, task_id))
    _typing_tasks[task_id] = task
    return task_id


def parar_digitando(task_id: str):
    """Cancela o indicador de digitando."""
    task = _typing_tasks.pop(task_id, None)
    if task and not task.done():
        task.cancel()


# ══════════════════════════════════════════════
# 👤  REGISTRO DE INTERAÇÃO (com telefone)
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
        phone = user.phone if hasattr(user, 'phone') and user.phone else None
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if uid not in db:
            db[uid] = {
                "id": user.id,
                "nome_atual": nome,
                "username_atual": username,
                "grupos": [],
                "primeiro_registro": agora,
                "historico": [],
                "origem": "interacao_bot"
            }
            if phone:
                db[uid]["telefone"] = phone
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
            if phone and not db[uid].get("telefone"):
                db[uid]["telefone"] = phone
                changed = True
            if changed:
                if len(db[uid]["historico"]) > MAX_HISTORY:
                    db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]
                salvar_dados(db)
    except Exception as e:
        log(f"⚠️ Erro ao registrar interação: {e}")


# ══════════════════════════════════════════════
# 📌  SUPORTE A TÓPICOS (Forum Threads)
# ══════════════════════════════════════════════

def get_reply_to(event) -> dict:
    """
    Retorna os kwargs corretos para responder no tópico configurado.
    Se o grupo tem tópico configurado, responde naquele tópico.
    Caso contrário, responde normalmente.
    """
    cfg = carregar_config()
    chat_id = str(event.chat_id)
    topicos = cfg.get("topicos", {})

    kwargs = {}

    # Se há tópico configurado para este chat
    if chat_id in topicos:
        topic_id = topicos[chat_id]
        kwargs["reply_to"] = topic_id

    # Se o evento veio de um tópico, responde no mesmo tópico
    elif hasattr(event, 'reply_to') and event.reply_to:
        reply_to_top_id = getattr(event.reply_to, 'reply_to_top_id', None)
        reply_to_msg_id = getattr(event.reply_to, 'reply_to_msg_id', None)
        topic = reply_to_top_id or reply_to_msg_id
        if topic:
            kwargs["reply_to"] = topic

    return kwargs


async def responder_evento(event, texto, parse_mode='md', buttons=None):
    """Responde ao evento no tópico correto, mencionando o usuário."""
    sender = await event.get_sender()
    mention = ""
    if sender and not event.is_private:
        nome = sender.first_name or "Usuário"
        mention = f"[{nome}](tg://user?id={sender.id}), "

    reply_kwargs = get_reply_to(event)

    if not event.is_private:
        texto_final = f"{mention}{texto}" if mention else texto
    else:
        texto_final = texto

    await event.respond(
        texto_final,
        parse_mode=parse_mode,
        buttons=buttons,
        **reply_kwargs
    )


# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════
async def notificar(texto: str):
    try:
        await bot.send_message(OWNER_ID, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")


async def notificar_grupo(chat_id: int, texto: str):
    """Notifica um grupo sobre alteração de perfil (se o bot for admin)."""
    try:
        # Verifica se o bot é admin no grupo
        me = await bot.get_me()
        try:
            participant = await bot(GetParticipantRequest(chat_id, me.id))
            is_admin_in_group = isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator))
        except Exception:
            is_admin_in_group = False

        if is_admin_in_group:
            cfg = carregar_config()
            topic_id = cfg.get("topicos", {}).get(str(chat_id))
            kwargs = {}
            if topic_id:
                kwargs["reply_to"] = topic_id
            await bot.send_message(chat_id, texto, parse_mode='md', **kwargs)
    except Exception as e:
        log(f"⚠️ Erro ao notificar grupo {chat_id}: {e}")


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
             Button.inline("👋 Boas-Vindas", b"cmd_set_welcome")]
        )
        btns.append(
            [Button.inline("🛡️ Controle de Abuso", b"cmd_abuse_panel"),
             Button.inline("📂 Grupos do Bot", b"cmd_grupos_bot")]
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
        # Mostra até 5 botões de páginas intermediárias
        step = max(1, total_pages // 5)
        pages_to_show = set()
        for i in range(0, total_pages, step):
            pages_to_show.add(i)
        pages_to_show.add(total_pages - 1)
        pages_to_show.discard(page)  # Remove a página atual
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
        # Também busca por telefone
        telefone = dados.get("telefone", "")
        if query_lower in nome or query_lower in username or (telefone and query_lower in telefone):
            results.append(dados)

    return results


def formatar_perfil(dados: dict) -> str:
    uid = dados.get("id", "?")
    nome = dados.get("nome_atual", "Desconhecido")
    username = dados.get("username_atual", "Nenhum")
    historico = dados.get("historico", [])
    grupos = dados.get("grupos", [])
    total_changes = len(historico)
    telefone = dados.get("telefone", None)
    bio = dados.get("bio", None)
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

    # Campos extras
    extras = ""
    if telefone:
        extras += f"📱 **Telefone:** `{telefone}`\n"
    if bio:
        extras += f"📝 **Bio:** _{bio}_\n"
    if origem:
        origem_emoji = {"api_telegram": "📡", "varredura": "🔄", "interacao_bot": "💬"}.get(origem, "📋")
        extras += f"{origem_emoji} **Origem:** {origem}\n"

    return f"""╔══════════════════════════╗
║  🕵️ **PERFIL DO USUÁRIO**  ║
╚══════════════════════════╝

👤 **Nome:** `{nome}`
🆔 **Username:** `{username}`
🔢 **ID:** `{uid}`
{extras}
📊 **Resumo:**
├ 📝 Total de alterações: **{total_changes}**
├ 📅 Primeiro registro: `{first_seen}`
├ 🕐 Última alteração: `{last_change}`
└ 📂 Grupos: **{len(grupos)}**

📂 **Grupos onde está presente:**
{grupos_text}
📜 **Últimas Alterações:**
{hist_text}
_Créditos: @Edkd1_"""


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
            # Coleta todos os diálogos de uma vez (mais rápido)
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

                try:
                    # Varredura em lotes — mais rápida
                    participants = []
                    try:
                        async for user in user_client.iter_participants(dialog.id, limit=SCAN_BATCH_SIZE * 10):
                            if user.bot:
                                continue
                            participants.append(user)
                    except Exception:
                        # Alguns grupos não permitem listar participantes
                        continue

                    for user in participants:
                        uid = str(user.id)
                        nome_atual = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome"
                        user_atual = f"@{user.username}" if user.username else "Nenhum"
                        phone = user.phone if hasattr(user, 'phone') and user.phone else None
                        scan_stats["users_scanned"] += 1

                        if uid not in db:
                            db[uid] = {
                                "id": user.id,
                                "nome_atual": nome_atual,
                                "username_atual": user_atual,
                                "grupos": [nome_grupo],
                                "primeiro_registro": agora,
                                "historico": [],
                                "origem": "varredura"
                            }
                            if phone:
                                db[uid]["telefone"] = phone
                        else:
                            if uid.startswith("_"):
                                continue
                            # Atualiza lista de grupos
                            if "grupos" not in db[uid]:
                                db[uid]["grupos"] = []
                            if nome_grupo not in db[uid]["grupos"]:
                                db[uid]["grupos"].append(nome_grupo)
                            
                            # Salva telefone se disponível
                            if phone and not db[uid].get("telefone"):
                                db[uid]["telefone"] = phone

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
                                # Notifica o dono
                                await notificar(
                                    f"🔔 **ALTERAÇÃO DE NOME**\n\n"
                                    f"👤 ID: `{uid}`\n"
                                    f"❌ Antigo: `{db[uid]['nome_atual']}`\n"
                                    f"✅ Novo: `{nome_atual}`\n"
                                    f"📍 Grupo: _{nome_grupo}_"
                                )
                                # Notifica o grupo (se bot for admin)
                                await notificar_grupo(
                                    chat_id_grupo,
                                    f"🔔 **Alteração detectada:**\n"
                                    f"👤 `{db[uid]['nome_atual']}` ➜ `{nome_atual}`\n"
                                    f"🆔 ID: `{uid}`"
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
                                await notificar(
                                    f"🆔 **MUDANÇA DE USERNAME**\n\n"
                                    f"👤 Nome: `{nome_atual}`\n"
                                    f"❌ Antigo: `{db[uid]['username_atual']}`\n"
                                    f"✅ Novo: `{user_atual}`\n"
                                    f"📍 Grupo: _{nome_grupo}_"
                                )
                                # Notifica o grupo
                                await notificar_grupo(
                                    chat_id_grupo,
                                    f"🆔 **Username alterado:**\n"
                                    f"👤 `{nome_atual}`\n"
                                    f"❌ `{db[uid]['username_atual']}` ➜ ✅ `{user_atual}`"
                                )
                                db[uid]["username_atual"] = user_atual

                            # Limita histórico
                            if len(db[uid]["historico"]) > MAX_HISTORY:
                                db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]

                    # Delay menor entre grupos para varredura rápida
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
_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )


# ══════════════════════════════════════════════
# 🎮  HANDLERS DO BOT
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    global scan_paused
    scan_paused = True  # Pausa varredura durante interação
    await registrar_interacao(event)
    sender = await event.get_sender()
    uid = sender.id if sender else 0
    await responder_evento(
        event,
        f"""╔══════════════════════════════╗
║  🕵️ **User Info Bot Pro v7.0**  ║
╚══════════════════════════════╝

Bem-vindo ao monitor profissional de usuários!

🔍 **Busque** por ID, @username ou nome
📊 **Monitore** alterações em tempo real
📜 **Histórico** completo de mudanças
📂 **Grupos** onde o usuário está presente
📡 **Consulta API** — busca em tempo real

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: Edivaldo Silva @Edkd1_
⚡ _Powered by 773H — v7.0 PRO_
━━━━━━━━━━━━━━━━━━━━━

Selecione uma opção abaixo:""",
        buttons=menu_principal_buttons(uid)
    )
    scan_paused = False  # Retoma varredura


@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await registrar_interacao(event)
    await cmd_start(event)


# ══════════════════════════════════════════════
# 📌  COMANDO: Configurar Tópico
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/settopic\s*(\d*)'))
async def cmd_set_topic(event):
    if not is_admin(event.sender_id):
        return
    await registrar_interacao(event)

    if event.is_private:
        await responder_evento(event, "⚠️ Este comando só funciona em **grupos com tópicos**.")
        return

    topic_id = event.pattern_match.group(1)
    cfg = carregar_config()
    chat_id = str(event.chat_id)

    if topic_id:
        cfg.setdefault("topicos", {})[chat_id] = int(topic_id)
        salvar_config(cfg)
        await responder_evento(event, f"✅ Tópico **{topic_id}** configurado para este grupo!")
    else:
        # Tenta detectar o tópico atual
        if hasattr(event, 'reply_to') and event.reply_to:
            detected = getattr(event.reply_to, 'reply_to_top_id', None) or getattr(event.reply_to, 'reply_to_msg_id', None)
            if detected:
                cfg.setdefault("topicos", {})[chat_id] = detected
                salvar_config(cfg)
                await responder_evento(event, f"✅ Tópico **{detected}** detectado e configurado!")
                return
        await responder_evento(event, "📌 Use `/settopic ID` ou envie o comando **dentro do tópico** desejado.")


@bot.on(events.NewMessage(pattern='/unsettopic'))
async def cmd_unset_topic(event):
    if not is_admin(event.sender_id):
        return
    cfg = carregar_config()
    chat_id = str(event.chat_id)
    if chat_id in cfg.get("topicos", {}):
        del cfg["topicos"][chat_id]
        salvar_config(cfg)
        await responder_evento(event, "✅ Tópico removido. O bot responderá normalmente.")
    else:
        await responder_evento(event, "ℹ️ Nenhum tópico configurado para este grupo.")


# ══════════════════════════════════════════════
# 📂  COMANDO: Listar Grupos do Bot (Admin)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/gruposbot'))
async def cmd_grupos_bot(event):
    """Lista todos os grupos onde o bot foi adicionado."""
    await registrar_interacao(event)
    if not is_admin(event.sender_id):
        await responder_evento(event, "🔒 Apenas o administrador pode ver os grupos do bot.")
        return

    grupos = carregar_grupos_bot()
    if not grupos:
        await responder_evento(event, "📂 O bot ainda não foi adicionado a nenhum grupo.", buttons=voltar_button())
        return

    ativos = {k: v for k, v in grupos.items() if v.get("ativo", True)}
    inativos = {k: v for k, v in grupos.items() if not v.get("ativo", True)}

    text = f"📂 **GRUPOS DO BOT** — {len(ativos)} ativos, {len(inativos)} removidos\n\n"
    
    for gid, info in list(ativos.items())[:15]:
        text += f"✅ **{info['nome']}**\n"
        text += f"   🔢 ID: `{info['id']}`\n"
        text += f"   🆔 Username: `{info['username']}`\n"
        text += f"   🔗 Link: `{info['link']}`\n"
        text += f"   📅 Desde: `{info.get('adicionado_em', 'N/A')}`\n\n"

    if inativos:
        text += f"\n🚫 **Removidos ({len(inativos)}):**\n"
        for gid, info in list(inativos.items())[:5]:
            text += f"   ❌ {info['nome']} — removido em `{info.get('removido_em', '?')}`\n"

    text += f"\n_Total: {len(grupos)} grupos registrados_\n_Créditos: @Edkd1_"
    await responder_evento(event, text, buttons=voltar_button())


# ══════════════════════════════════════════════
# 👋  COMANDO: Boas-Vindas Customizáveis
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/setwelcome\s+(.+)', func=lambda e: not e.is_private))
async def cmd_set_welcome(event):
    """Define mensagem de boas-vindas. Variáveis: {mention}, {nome}, {grupo}, {id}"""
    # Verifica se quem enviou é dono/admin do grupo
    sender = await event.get_sender()
    try:
        participant = await bot(GetParticipantRequest(event.chat_id, sender.id))
        is_group_admin = isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator))
    except Exception:
        is_group_admin = False

    if not is_group_admin and not is_admin(sender.id):
        await responder_evento(event, "🔒 Apenas administradores do grupo podem configurar boas-vindas.")
        return

    msg = event.pattern_match.group(1).strip()
    cfg = carregar_config()
    cfg.setdefault("boas_vindas", {})[str(event.chat_id)] = msg
    salvar_config(cfg)
    await responder_evento(
        event,
        f"✅ **Boas-vindas configuradas!**\n\n"
        f"📝 Mensagem: _{msg}_\n\n"
        f"💡 Variáveis: `{{mention}}`, `{{nome}}`, `{{grupo}}`, `{{id}}`"
    )


@bot.on(events.NewMessage(pattern='/unsetwelcome', func=lambda e: not e.is_private))
async def cmd_unset_welcome(event):
    sender = await event.get_sender()
    try:
        participant = await bot(GetParticipantRequest(event.chat_id, sender.id))
        is_group_admin = isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator))
    except Exception:
        is_group_admin = False

    if not is_group_admin and not is_admin(sender.id):
        return

    cfg = carregar_config()
    chat_id = str(event.chat_id)
    if chat_id in cfg.get("boas_vindas", {}):
        del cfg["boas_vindas"][chat_id]
        salvar_config(cfg)
        await responder_evento(event, "✅ Boas-vindas removidas. Mensagem padrão restaurada.")
    else:
        await responder_evento(event, "ℹ️ Nenhuma mensagem personalizada configurada.")


# ══════════════════════════════════════════════
# 👋  HANDLER: Novos Membros + Bot Adicionado
# ══════════════════════════════════════════════

@bot.on(events.ChatAction)
async def welcome_handler(event):
    """Saúda novos membros e registra quando o bot é adicionado a um grupo."""
    try:
        chat = await event.get_chat()
        chat_id = str(event.chat_id)

        # ── Detecta se O BOT foi adicionado ao grupo ──
        if event.user_added or event.user_joined:
            user = await event.get_user()
            if not user:
                return

            me = await bot.get_me()
            if user.id == me.id:
                # Bot foi adicionado! Registra o grupo
                adicionado_por_info = None
                if event.user_added:
                    try:
                        adder = await event.get_added_by()
                        if adder:
                            adicionado_por_info = f"{adder.first_name or ''} ({adder.id})"
                    except Exception:
                        pass
                await registrar_grupo_bot(chat, adicionado_por=adicionado_por_info)
                
                # Mensagem de apresentação no chat principal
                grupo_nome = getattr(chat, 'title', 'Grupo')
                await bot.send_message(
                    event.chat_id,
                    f"👋 **Olá, {grupo_nome}!**\n\n"
                    f"Sou o **User Info Bot Pro v7.0** 🕵️\n\n"
                    f"📋 **O que eu faço:**\n"
                    f"• 👋 Saúdo novos membros automaticamente\n"
                    f"• 🔍 Busco informações de usuários\n"
                    f"• 📊 Monitoro alterações de perfil\n\n"
                    f"⚙️ **Para o dono do grupo:**\n"
                    f"• `/setwelcome Sua mensagem` — Personalizar boas-vindas\n"
                    f"• `/unsetwelcome` — Restaurar padrão\n"
                    f"• `/regras` — Exibir regras do grupo\n\n"
                    f"💡 Variáveis: `{{mention}}`, `{{nome}}`, `{{grupo}}`, `{{id}}`\n\n"
                    f"_Créditos: @Edkd1_",
                    parse_mode='md'
                )
                return

            # ── Usuário normal entrou — saudação ──
            if user.bot:
                return

            grupo_nome = getattr(chat, 'title', 'Grupo')
            nome = user.first_name or "Novo membro"
            mention = f"[{nome}](tg://user?id={user.id})"

            # Registra o usuário no banco
            uid = str(user.id)
            db = carregar_dados()
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            if uid not in db:
                username = f"@{user.username}" if user.username else "Nenhum"
                db[uid] = {
                    "id": user.id,
                    "nome_atual": f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome",
                    "username_atual": username,
                    "grupos": [grupo_nome],
                    "primeiro_registro": agora,
                    "historico": [],
                    "origem": "entrada_grupo"
                }
                if hasattr(user, 'phone') and user.phone:
                    db[uid]["telefone"] = user.phone
                salvar_dados(db)
            else:
                if "grupos" not in db[uid]:
                    db[uid]["grupos"] = []
                if grupo_nome not in db[uid]["grupos"]:
                    db[uid]["grupos"].append(grupo_nome)
                    salvar_dados(db)

            # Registra o grupo também
            await registrar_grupo_bot(chat)

            # Mensagem de boas-vindas — SEMPRE no chat principal (sem reply_to tópico)
            cfg = carregar_config()
            msg_template = cfg.get("boas_vindas", {}).get(chat_id)

            if msg_template:
                try:
                    msg = msg_template.format(
                        mention=mention,
                        nome=nome,
                        grupo=grupo_nome,
                        id=user.id
                    )
                except (KeyError, IndexError):
                    msg = msg_template  # Se template inválido, envia como está
            else:
                msg = (
                    f"👋 {mention} seja bem-vindo(a) ao **{grupo_nome}**! 🎉\n"
                    f"Use `/regras` para ver as regras do grupo."
                )

            # Envia NO CHAT PRINCIPAL (sem reply_to para não ir em tópico)
            await bot.send_message(event.chat_id, msg, parse_mode='md')

        # ── Detecta se o bot foi removido do grupo ──
        elif event.user_left or event.user_kicked:
            user = await event.get_user()
            if user:
                me = await bot.get_me()
                if user.id == me.id:
                    grupos = carregar_grupos_bot()
                    if chat_id in grupos:
                        grupos[chat_id]["ativo"] = False
                        grupos[chat_id]["removido_em"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        salvar_grupos_bot(grupos)
                    grupo_nome = getattr(chat, 'title', 'Grupo')
                    await notificar(f"🚫 **Bot removido do grupo:** {grupo_nome} (`{chat_id}`)")

    except Exception as e:
        log(f"⚠️ Erro no welcome/group handler: {e}")


# ══════════════════════════════════════════════
# 📜  COMANDO: Regras do Grupo
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/regras', func=lambda e: not e.is_private))
async def cmd_regras(event):
    """Exibe as regras do grupo (extraídas da descrição/about do grupo)."""
    await registrar_interacao(event)

    try:
        chat = await bot.get_entity(event.chat_id)
        full_chat = await bot(GetFullUserRequest(chat.id)) if hasattr(chat, 'id') else None

        # Tenta obter a descrição do grupo
        try:
            from telethon.tl.functions.channels import GetFullChannelRequest
            from telethon.tl.functions.messages import GetFullChatRequest

            if hasattr(chat, 'megagroup') or hasattr(chat, 'broadcast'):
                full = await bot(GetFullChannelRequest(chat))
                about = full.full_chat.about or ""
            else:
                full = await bot(GetFullChatRequest(chat.id))
                about = full.full_chat.about or ""
        except Exception:
            about = ""

        if about:
            await responder_evento(
                event,
                f"""📜 **REGRAS DO GRUPO**

╔══════════════════════════╗
║  📋 {getattr(chat, 'title', 'Grupo')}
╚══════════════════════════╝

{about}

━━━━━━━━━━━━━━━━━━━━━
_Respeite as regras para uma boa convivência!_"""
            )
        else:
            await responder_evento(event, "ℹ️ Este grupo não possui regras definidas na descrição.")

    except Exception as e:
        log(f"⚠️ Erro ao buscar regras: {e}")
        await responder_evento(event, "⚠️ Não foi possível obter as regras do grupo.")


# ══════════════════════════════════════════════
# 🔍  BUSCA VIA @InforUser_Bot + termo (em grupos)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=rf'@{BOT_USERNAME}\s+(.+)', func=lambda e: not e.is_private))
async def cmd_buscar_mention(event):
    """Busca ativada por @InforUser_Bot + termo no grupo."""
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)

    # Verifica abuso
    abuse = verificar_abuso(event.sender_id)
    if not abuse["permitido"]:
        sender = await event.get_sender()
        await responder_evento(event, abuse["motivo"])
        if abuse["avisos"] > 0:
            nome = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
            username = f"@{sender.username}" if sender.username else "Nenhum"
            await notificar_abuso(sender.id, nome, username, "busca via menção", abuse["avisos"])
        scan_paused = False
        return

    query = event.pattern_match.group(1).strip()
    results = buscar_usuario(query)

    if not results:
        # Consulta via API do Telegram
        await responder_evento(event, f"🔍 Buscando `{query}` via API do Telegram...\n⏳ _Aguarde..._")
        api_result = await consultar_api_telegram(query, event)
        if api_result:
            results = [api_result]
        else:
            await responder_evento(
                event,
                f"❌ **Nenhum resultado para** `{query}`\n\n💡 Tente buscar por ID numérico, @username ou nome.",
                buttons=voltar_button()
            )
            scan_paused = False
            return

    if len(results) == 1:
        await responder_evento(event, formatar_perfil(results[0]), buttons=[
            [Button.inline("📜 Histórico", f"hist_{results[0]['id']}_0".encode()),
             Button.inline("📂 Grupos", f"ugroups_{results[0]['id']}_0".encode())],
            [Button.inline("🔙 Menu", b"cmd_menu")]
        ])
    else:
        text = f"🔍 **{len(results)} resultados para** `{query}`:\n\n"
        btns = []
        for r in results[:ITEMS_PER_PAGE]:
            label = f"👤 {r['nome_atual']} | {r['username_atual']}"
            btns.append([Button.inline(label[:40], f"profile_{r['id']}".encode())])
        btns.append([Button.inline("🔙 Menu", b"cmd_menu")])
        await responder_evento(event, text, buttons=btns)

    scan_paused = False


# ══════════════════════════════════════════════
# 🔍  BUSCA VIA COMANDO /buscar
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/buscar\s+(.+)'))
async def cmd_buscar_text(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)

    # Verifica abuso
    abuse = verificar_abuso(event.sender_id)
    if not abuse["permitido"]:
        sender = await event.get_sender()
        await responder_evento(event, abuse["motivo"])
        if abuse["avisos"] > 0:
            nome = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
            username = f"@{sender.username}" if sender.username else "Nenhum"
            await notificar_abuso(sender.id, nome, username, "comando /buscar", abuse["avisos"])
        scan_paused = False
        return

    query = event.pattern_match.group(1).strip()
    results = buscar_usuario(query)

    if not results:
        # Fallback: consulta via API do Telegram
        await responder_evento(event, f"🔍 Não encontrado no banco. Consultando API do Telegram...\n⏳ _Aguarde..._")
        api_result = await consultar_api_telegram(query, event)
        if api_result:
            results = [api_result]
        else:
            await responder_evento(
                event,
                "❌ **Nenhum usuário encontrado.**\n\n💡 Tente buscar por ID numérico, @username ou parte do nome.",
                buttons=voltar_button()
            )
            scan_paused = False
            return

    if len(results) == 1:
        await responder_evento(event, formatar_perfil(results[0]), buttons=[
            [Button.inline(f"📜 Histórico Completo", f"hist_{results[0]['id']}_0".encode())],
            [Button.inline(f"📂 Ver Grupos", f"ugroups_{results[0]['id']}_0".encode())],
            [Button.inline("🔙 Menu Principal", b"cmd_menu")]
        ])
    else:
        # Múltiplos resultados — paginação com 10 por página
        await mostrar_resultados_busca(event, query, results, 0)
    scan_paused = False


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
# 🔘  HANDLERS DE CALLBACK (BOTÕES INLINE)
# ══════════════════════════════════════════════

search_pending = {}
last_search_results = {}  # Cache dos resultados de busca para paginação

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    global scan_paused
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    # Pausa a varredura durante interação com o bot
    scan_paused = True

    try:
        message = await event.get_message()

        # ── Menu Principal ──
        if data == "cmd_menu":
            await message.edit(
                f"""╔══════════════════════════════╗
║  🕵️ **User Info Bot Pro v7.0**  ║
╚══════════════════════════════╝

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Buscar ──
        elif data == "cmd_buscar":
            search_pending[chat_id] = True
            await message.edit(
                """🔍 **Modo de Busca Ativo**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie** um dos seguintes:

• 🔢 **ID numérico** — ex: `123456789`
• 🆔 **@username** — ex: `@exemplo`
• 📛 **Nome** (parcial) — ex: `João`
• 📱 **Telefone** — ex: `5511999999999`

━━━━━━━━━━━━━━━━━━━━━
_Ou use @InforUser_Bot + termo em qualquer chat_
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
            total_phones = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("telefone"))
            total_api = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("origem") == "api_telegram")

            with_history = sum(1 for k, d in db.items() if not k.startswith("_") and d.get("historico"))
            groups = set()
            for k, d in db.items():
                if not k.startswith("_"):
                    groups.update(d.get("grupos", []))

            last = scan_stats.get("last_scan", "Nunca")
            meta = db.get("_meta", {})
            total_scans = meta.get("total_varreduras", 0)

            # Contagem de abuso
            cfg = carregar_config()
            total_banidos = len(cfg.get("usuarios_banidos", {}))

            await message.edit(
                f"""╔══════════════════════════╗
║  📊 **ESTATÍSTICAS**       ║
╚══════════════════════════╝

👥 **Banco de Dados:**
├ 📋 Total de usuários: **{total_users}**
├ 📂 Grupos monitorados: **{len(groups)}**
├ 🔔 Usuários com alterações: **{with_history}**
├ 📱 Com telefone registrado: **{total_phones}**
├ 📡 Obtidos via API: **{total_api}**
└ 📊 Cobertura: **{(with_history/total_users*100) if total_users else 0:.1f}%**

📝 **Alterações Registradas:**
├ 📛 Mudanças de nome: **{total_names}**
├ 🆔 Mudanças de username: **{total_usernames}**
└ 📊 Total: **{total_changes}**

⚙️ **Sistema:**
├ 🕐 Última varredura: `{last}`
├ 🔄 Total de varreduras: **{total_scans}**
├ 🔄 Intervalo: `{SCAN_INTERVAL // 60} min`
├ 📄 Itens/página: **{ITEMS_PER_PAGE}**
├ 🛡️ Usuários banidos: **{total_banidos}**
└ 💾 Tamanho do banco: **{os.path.getsize(FILE_PATH) // 1024 if os.path.exists(FILE_PATH) else 0} KB**

_Créditos: @Edkd1_""",
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
                scan_paused = False  # Despausa para a varredura funcionar
                asyncio.create_task(executar_varredura(notify_chat=chat_id))
                return  # Não retomar a pausa

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
                    caption="📤 **Banco de dados exportado com sucesso!**\n\n_Créditos: @Edkd1_",
                    parse_mode='md'
                )
                await event.answer("✅ Arquivo enviado!")
            else:
                await event.answer("❌ Banco vazio!", alert=True)

        # ── Configurações ──
        elif data == "cmd_config":
            cfg = carregar_config()
            topicos_count = len(cfg.get("topicos", {}))
            welcome_count = len(cfg.get("boas_vindas", {}))
            banidos_count = len(cfg.get("usuarios_banidos", {}))

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

🔧 **Recursos v7.0 PRO:**
• ⚡ Varredura otimizada em lotes
• 🔒 Pausa automática durante uso
• 📂 Rastreamento de grupos
• 📄 Paginação completa (10/pág)
• 🆕 Criação automática do banco
• 📡 Consulta API do Telegram
• 📌 Suporte a Tópicos ({topicos_count} configurados)
• 👋 Boas-vindas ({welcome_count} grupos)
• 🛡️ Controle de Abuso ({banidos_count} banidos)
• 📱 Captura de telefone
• 🔍 Busca via @{BOT_USERNAME}

━━━━━━━━━━━━━━━━━━━━━

**Comandos de Configuração:**
• `/settopic [ID]` — Configura tópico
• `/unsettopic` — Remove tópico
• `/setwelcome [msg]` — Configura boas-vindas
• `/unsetwelcome` — Remove boas-vindas

_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )

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
            await event.answer("✅ Cache limpo!", alert=True)

        # ── Configurar Tópico (via botão) ──
        elif data == "cmd_set_topic":
            await message.edit(
                """📌 **Configurar Tópico**

━━━━━━━━━━━━━━━━━━━━━
Use os comandos:

• `/settopic [ID]` — Define o tópico pelo ID
• `/settopic` — Detecta automaticamente (envie dentro do tópico)
• `/unsettopic` — Remove configuração

━━━━━━━━━━━━━━━━━━━━━
💡 O bot responderá apenas no tópico configurado.""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Boas-Vindas (via botão) ──
        elif data == "cmd_set_welcome":
            await message.edit(
                """👋 **Configurar Boas-Vindas**

━━━━━━━━━━━━━━━━━━━━━
Use os comandos **dentro do grupo**:

• `/setwelcome Bem-vindo, {mention}! 🎉`
• `/unsetwelcome` — Remove personalização

**Variáveis disponíveis:**
• `{mention}` — Menção do usuário
• `{nome}` — Nome do usuário
• `{grupo}` — Nome do grupo
• `{id}` — ID do usuário

━━━━━━━━━━━━━━━━━━━━━
💡 O dono do grupo também pode configurar.""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Grupos do Bot (via botão) ──
        elif data == "cmd_grupos_bot":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                scan_paused = False
                return
            grupos = carregar_grupos_bot()
            if not grupos:
                await message.edit("📂 O bot ainda não foi adicionado a nenhum grupo.", parse_mode='md', buttons=voltar_button())
            else:
                ativos = {k: v for k, v in grupos.items() if v.get("ativo", True)}
                text = f"📂 **GRUPOS DO BOT** — {len(ativos)} ativos\n\n"
                for gid, info in list(ativos.items())[:10]:
                    text += f"✅ **{info['nome']}**\n"
                    text += f"   🔢 `{info['id']}` | 🆔 `{info['username']}`\n"
                    text += f"   🔗 `{info['link']}`\n\n"
                text += f"_Total: {len(grupos)} grupos_\n_Use /gruposbot para detalhes_"
                await message.edit(text, parse_mode='md', buttons=voltar_button())

        # ── Painel de Abuso ──
        elif data == "cmd_abuse_panel":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                scan_paused = False
                return

            cfg = carregar_config()
            banidos = cfg.get("usuarios_banidos", {})

            if not banidos:
                text = "🛡️ **Controle de Abuso**\n\n✅ Nenhum usuário banido ou com avisos."
            else:
                text = f"🛡️ **Controle de Abuso** — {len(banidos)} registros\n\n"
                for uid, info in list(banidos.items())[:10]:
                    db = carregar_dados()
                    nome = db.get(uid, {}).get("nome_atual", "Desconhecido")
                    ban_ate = info.get("ate", 0)
                    avisos = info.get("avisos", 0)
                    status = "🚫 Banido" if ban_ate > time.time() else f"⚠️ {avisos} avisos"
                    text += f"• `{uid}` — {nome} — {status}\n"

            btns = [[Button.inline("🔄 Atualizar", b"cmd_abuse_panel")],
                    [Button.inline("🔙 Menu", b"cmd_menu")]]
            await message.edit(text, parse_mode='md', buttons=btns)

        # ── Ações de Abuso (Admin) ──
        elif data.startswith("abuse_warn_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                scan_paused = False
                return
            target_id = int(data.replace("abuse_warn_", ""))
            try:
                await bot.send_message(
                    target_id,
                    "⚠️ **AVISO DO ADMINISTRADOR**\n\n"
                    "Você está usando o bot de forma excessiva.\n"
                    "Por favor, aguarde alguns segundos entre os comandos.\n\n"
                    "⚠️ Uso contínuo pode resultar em banimento temporário.\n\n"
                    "_Administração @Edkd1_",
                    parse_mode='md'
                )
                await event.answer("✅ Aviso enviado!", alert=True)
            except Exception:
                await event.answer("❌ Não foi possível enviar aviso.", alert=True)

        elif data.startswith("abuse_ban_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            parts = data.split("_")
            target_id = parts[2]
            duration = int(parts[3])
            cfg = carregar_config()
            cfg.setdefault("usuarios_banidos", {})[target_id] = {
                "ate": time.time() + duration,
                "avisos": ABUSE_WARN_THRESHOLD,
                "banido_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            salvar_config(cfg)
            try:
                await bot.send_message(
                    int(target_id),
                    f"🚫 **BANIDO TEMPORARIAMENTE**\n\n"
                    f"Duração: **{duration // 3600}h**\n"
                    f"Motivo: Uso excessivo do bot.\n\n"
                    f"_Administração @Edkd1_",
                    parse_mode='md'
                )
            except Exception:
                pass
            await event.answer(f"🚫 Banido por {duration // 3600}h!", alert=True)

        elif data.startswith("abuse_unban_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            target_id = data.replace("abuse_unban_", "")
            cfg = carregar_config()
            if target_id in cfg.get("usuarios_banidos", {}):
                del cfg["usuarios_banidos"][target_id]
                salvar_config(cfg)
                await event.answer("✅ Usuário desbloqueado!", alert=True)
            else:
                await event.answer("ℹ️ Usuário não está banido.", alert=True)

        elif data.startswith("abuse_log_"):
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                scan_paused = False
                return
            target_id = data.replace("abuse_log_", "")
            cfg = carregar_config()
            db = carregar_dados()
            nome = db.get(target_id, {}).get("nome_atual", "Desconhecido")
            username = db.get(target_id, {}).get("username_atual", "Nenhum")
            logs = cfg.get("abuse_log", {}).get(target_id, [])
            ban_info = cfg.get("usuarios_banidos", {}).get(target_id, {})

            text = f"""📊 **Log de Interações**

👤 **Nome:** `{nome}`
🆔 **Username:** `{username}`
🔢 **ID:** `{target_id}`
📊 **Comandos recentes:** {len(logs)}
⚠️ **Avisos:** {ban_info.get('avisos', 0)}/{ABUSE_WARN_THRESHOLD}
🚫 **Banido:** {'Sim' if ban_info.get('ate', 0) > time.time() else 'Não'}
"""
            if ban_info.get("banido_em"):
                text += f"📅 **Banido em:** `{ban_info['banido_em']}`\n"

            await message.edit(text, parse_mode='md', buttons=[
                [Button.inline("⚠️ Enviar Aviso", f"abuse_warn_{target_id}".encode()),
                 Button.inline("🚫 Banir 1h", f"abuse_ban_{target_id}_3600".encode())],
                [Button.inline("✅ Desbloquear", f"abuse_unban_{target_id}".encode()),
                 Button.inline("🔙 Voltar", b"cmd_abuse_panel")]
            ])

        # ── Sobre ──
        elif data == "cmd_about":
            await message.edit(
                f"""╔══════════════════════════════╗
║  ℹ️ **SOBRE O BOT**           ║
╚══════════════════════════════╝

🕵️ **User Info Bot Pro v7.0**
_Monitor profissional de usuários_

━━━━━━━━━━━━━━━━━━━━━
**Funcionalidades:**
• 🔍 Busca por ID, @user, nome ou telefone
• 📡 Consulta API do Telegram em tempo real
• 📡 Varredura rápida otimizada
• 🔔 Notificações de alterações (grupos + DM)
• 📜 Histórico paginado (10/pág)
• 📂 Rastreamento de grupos
• 📤 Exportação de dados
• 📊 Estatísticas detalhadas
• 🔒 Pausa durante interações
• 🆕 Auto-criação do banco
• 📌 Suporte a Tópicos (forum threads)
• 👋 Boas-vindas no chat principal (personalizáveis)
• 📜 Regras do grupo (/regras)
• 🛡️ Controle de abuso (rate limit + ban)
• 📱 Captura de telefone
• 🔍 Busca via @{BOT_USERNAME} + termo
• 📂 Registro automático de grupos (/gruposbot)
• 🚪 Detecta entrada/saída do bot em grupos
• ⚡ Cache em memória para respostas rápidas

**Tecnologia:**
• ⚡ Telethon (asyncio) + Cache inteligente
• 💾 Banco JSON local + groups_bot.json
• 🛡️ Anti-flood + Anti-abuso
• 🔄 Lock de operações
• 📡 API Telegram fallback

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 **Criado por:** Edivaldo Silva
📱 **Contato:** @Edkd1
🔖 **Versão:** 7.0 PRO (773H Ultra)
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


# ── Handler: texto livre (busca quando modo ativo) ──
@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def text_handler(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)
    chat_id = event.chat_id

    # Verifica abuso
    abuse = verificar_abuso(event.sender_id)
    if not abuse["permitido"]:
        sender = await event.get_sender()
        await event.reply(abuse["motivo"], parse_mode='md')
        if abuse["avisos"] > 0:
            nome = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
            username = f"@{sender.username}" if sender.username else "Nenhum"
            await notificar_abuso(sender.id, nome, username, "texto livre", abuse["avisos"])
        scan_paused = False
        return

    if chat_id in search_pending:
        mode = search_pending.pop(chat_id)
        query = event.text.strip()
        results = buscar_usuario(query)

        if not results:
            # Fallback: API do Telegram
            await event.reply(f"🔍 Buscando `{query}` via API...\n⏳ _Aguarde..._", parse_mode='md')
            api_result = await consultar_api_telegram(query, event)
            if api_result:
                results = [api_result]
            else:
                await event.reply(
                    f"❌ **Nenhum resultado para** `{query}`\n\n💡 Tente outro termo.",
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
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ])
            else:
                # Salva resultados para paginação
                last_search_results[chat_id] = {"query": query, "results": results}
                await mostrar_resultados_busca(event, query, results, 0)
    else:
        await event.reply(
            "💡 Use o menu para navegar ou `/buscar termo` para buscar.\n"
            f"💡 Ou use `@{BOT_USERNAME} termo` em qualquer chat!",
            parse_mode='md',
            buttons=menu_principal_buttons(event.chat_id)
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

    log("🚀 User Info Bot Pro v7.0 PRO iniciado!")
    log("👨‍💻 Créditos: Edivaldo Silva @Edkd1")

    # Criação automática do banco na primeira execução
    primeiro_inicio = inicializar_banco()
    if primeiro_inicio:
        log("🆕 Primeira execução — banco criado automaticamente")
        await notificar(
            "🆕 **Primeira Execução!**\n\n"
            "✅ Banco de dados criado automaticamente.\n"
            "📡 Iniciando varredura inicial...\n\n"
            "_O bot estará operacional em instantes._"
        )

    # Inicializa config
    cfg = carregar_config()
    salvar_config(cfg)

    log(f"🔄 Varredura automática a cada {SCAN_INTERVAL // 60} min")
    log(f"📄 Paginação: {ITEMS_PER_PAGE} itens por página")
    log(f"📌 Tópicos configurados: {len(cfg.get('topicos', {}))}")
    log(f"👋 Boas-vindas: {len(cfg.get('boas_vindas', {}))}")
    log(f"🛡️ Controle de abuso: {ABUSE_MAX_COMMANDS} cmds/{ABUSE_WINDOW}s")
    log("📡 Executando primeira varredura...")

    # Primeira varredura ao iniciar
    await executar_varredura(notify_chat=OWNER_ID)

    # Agenda varreduras automáticas
    asyncio.create_task(auto_scanner())

    print("✅ Bot v7.0 PRO ativo! Use /start ou /buscar")
    await bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
