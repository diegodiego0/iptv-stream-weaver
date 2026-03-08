import json
import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest

# ══════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES
# ══════════════════════════════════════════════
API_ID = 29214781                        # Obtenha em https://my.telegram.org
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102                 # Edivaldo Silva @Edkd1

FOLDER_PATH = "data"
FILE_PATH = os.path.join(FOLDER_PATH, "user_database.json")
LOG_PATH = os.path.join(FOLDER_PATH, "monitor.log")
SESSION_USER = "session_monitor"
SESSION_BOT = "session_bot"

ITEMS_PER_PAGE = 10                   # 10 itens por página
SCAN_INTERVAL = 1800                  # Varredura a cada 30 min (mais rápido)
MAX_HISTORY = 50
SCAN_BATCH_SIZE = 200                 # Participantes por lote para varredura rápida
SCAN_BATCH_DELAY = 0.3               # Delay entre lotes (menor = mais rápido)
FLOOD_WAIT_MARGIN = 1.2              # Multiplicador de segurança para FloodWait

# ══════════════════════════════════════════════
# 📁  BANCO DE DADOS JSON — CRIAÇÃO AUTOMÁTICA
# ══════════════════════════════════════════════
os.makedirs(FOLDER_PATH, exist_ok=True)

def inicializar_banco():
    """Cria o banco de dados na primeira execução com estrutura padrão."""
    if not os.path.exists(FILE_PATH):
        estrutura_inicial = {
            "_meta": {
                "versao": "5.0",
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
            return {"_meta": {"versao": "5.0", "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}
    return {"_meta": {"versao": "5.0", "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "total_varreduras": 0, "ultimo_scan": None}}

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
            if changed:
                if len(db[uid]["historico"]) > MAX_HISTORY:
                    db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]
                salvar_dados(db)
    except Exception as e:
        log(f"⚠️ Erro ao registrar interação: {e}")


# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════
async def notificar(texto: str):
    try:
        await bot.send_message(OWNER_ID, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")


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
        if query_lower in nome or query_lower in username:
            results.append(dados)

    return results


def formatar_perfil(dados: dict) -> str:
    uid = dados.get("id", "?")
    nome = dados.get("nome_atual", "Desconhecido")
    username = dados.get("username_atual", "Nenhum")
    historico = dados.get("historico", [])
    grupos = dados.get("grupos", [])
    total_changes = len(historico)

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

    return f"""╔══════════════════════════╗
║  🕵️ **PERFIL DO USUÁRIO**  ║
╚══════════════════════════╝

👤 **Nome:** `{nome}`
🆔 **Username:** `{username}`
🔢 **ID:** `{uid}`

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
                        scan_stats["users_scanned"] += 1

                        if uid not in db:
                            db[uid] = {
                                "id": user.id,
                                "nome_atual": nome_atual,
                                "username_atual": user_atual,
                                "grupos": [nome_grupo],
                                "primeiro_registro": agora,
                                "historico": []
                            }
                        else:
                            if uid.startswith("_"):
                                continue
                            # Atualiza lista de grupos
                            if "grupos" not in db[uid]:
                                db[uid]["grupos"] = []
                            if nome_grupo not in db[uid]["grupos"]:
                                db[uid]["grupos"].append(nome_grupo)

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
                                await notificar(
                                    f"🔔 **ALTERAÇÃO DE NOME**\n\n"
                                    f"👤 ID: `{uid}`\n"
                                    f"❌ Antigo: `{db[uid]['nome_atual']}`\n"
                                    f"✅ Novo: `{nome_atual}`\n"
                                    f"📍 Grupo: _{nome_grupo}_"
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
    await event.respond(
        f"""╔══════════════════════════════╗
║  🕵️ **User Info Bot Pro v5.0**  ║
╚══════════════════════════════╝

Bem-vindo ao monitor profissional de usuários!

🔍 **Busque** por ID, @username ou nome
📊 **Monitore** alterações em tempo real
📜 **Histórico** completo de mudanças
📂 **Grupos** onde o usuário está presente

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: Edivaldo Silva @Edkd1_
⚡ _Powered by 773H — v5.0_
━━━━━━━━━━━━━━━━━━━━━

Selecione uma opção abaixo:""",
        parse_mode='md',
        buttons=menu_principal_buttons(uid)
    )
    scan_paused = False  # Retoma varredura


@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await registrar_interacao(event)
    await cmd_start(event)


@bot.on(events.NewMessage(pattern=r'/buscar\s+(.+)'))
async def cmd_buscar_text(event):
    global scan_paused
    scan_paused = True
    await registrar_interacao(event)
    query = event.pattern_match.group(1).strip()
    results = buscar_usuario(query)

    if not results:
        await event.reply(
            "❌ **Nenhum usuário encontrado.**\n\n💡 Tente buscar por ID numérico, @username ou parte do nome.",
            parse_mode='md',
            buttons=voltar_button()
        )
        scan_paused = False
        return

    if len(results) == 1:
        await event.reply(formatar_perfil(results[0]), parse_mode='md', buttons=[
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
║  🕵️ **User Info Bot Pro v5.0**  ║
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

━━━━━━━━━━━━━━━━━━━━━
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
            groups = set()
            for k, d in db.items():
                if not k.startswith("_"):
                    groups.update(d.get("grupos", []))

            last = scan_stats.get("last_scan", "Nunca")
            meta = db.get("_meta", {})
            total_scans = meta.get("total_varreduras", 0)

            await message.edit(
                f"""╔══════════════════════════╗
║  📊 **ESTATÍSTICAS**       ║
╚══════════════════════════╝

👥 **Banco de Dados:**
├ 📋 Total de usuários: **{total_users}**
├ 📂 Grupos monitorados: **{len(groups)}**
├ 🔔 Usuários com alterações: **{with_history}**
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

🔧 **Recursos v5.0:**
• ⚡ Varredura otimizada em lotes
• 🔒 Pausa automática durante uso
• 📂 Rastreamento de grupos
• 📄 Paginação completa (10/pág)
• 🆕 Criação automática do banco

_Para alterar, edite as constantes no código._
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

        # ── Sobre ──
        elif data == "cmd_about":
            await message.edit(
                """╔══════════════════════════════╗
║  ℹ️ **SOBRE O BOT**           ║
╚══════════════════════════════╝

🕵️ **User Info Bot Pro v5.0**
_Monitor profissional de usuários_

━━━━━━━━━━━━━━━━━━━━━
**Funcionalidades:**
• 🔍 Busca por ID, @user ou nome
• 📡 Varredura rápida otimizada
• 🔔 Notificações de alterações
• 📜 Histórico paginado (10/pág)
• 📂 Rastreamento de grupos
• 📤 Exportação de dados
• 📊 Estatísticas detalhadas
• 🔒 Pausa durante interações
• 🆕 Auto-criação do banco

**Tecnologia:**
• ⚡ Telethon (asyncio)
• 💾 Banco JSON local
• 🛡️ Anti-flood integrado
• 🔄 Lock de operações

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 **Criado por:** Edivaldo Silva
📱 **Contato:** @Edkd1
🔖 **Versão:** 5.0 (773H)
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

    if chat_id in search_pending:
        mode = search_pending.pop(chat_id)
        query = event.text.strip()
        results = buscar_usuario(query)

        if not results:
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
            "💡 Use o menu para navegar ou `/buscar termo` para buscar.",
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

    log("🚀 User Info Bot Pro v5.0 iniciado!")
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

    log(f"🔄 Varredura automática a cada {SCAN_INTERVAL // 60} min")
    log(f"📄 Paginação: {ITEMS_PER_PAGE} itens por página")
    log("📡 Executando primeira varredura...")

    # Primeira varredura ao iniciar
    await executar_varredura(notify_chat=OWNER_ID)

    # Agenda varreduras automáticas
    asyncio.create_task(auto_scanner())

    print("✅ Bot ativo! Use /start ou /buscar")
    await bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
