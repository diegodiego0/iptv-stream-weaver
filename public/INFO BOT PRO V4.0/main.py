# ══════════════════════════════════════════════
# 🚀  INFO BOT PRO V4.0 — MAIN
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
#
# Bot 100% funcional — ID detector, responde
# o usuário específico sem abuso de iteração.
#
# Estrutura modular:
#   main.py        → Bot principal + handlers
#   grupo.py       → Funções de grupos e varredura
#   pagina.py      → Paginação
#   botoes.py      → Botões inline
#   aplicativo.py  → API_ID, API_HASH, PHONE
#   token.json     → Token do bot
#
# Ciclo de varredura:
#   1. Varredura COMPLETA — todos os grupos um por um
#   2. Aguarda 2 minutos
#   3. Varredura LEVE (threads) — todos os grupos ligeiramente
#   4. Aguarda 2 minutos
#   5. Repete o ciclo
#
# ══════════════════════════════════════════════

import json
import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button

# ── Módulos locais ──
from aplicativo import API_ID, API_HASH, PHONE
from grupo import (
    carregar_dados, salvar_dados, carregar_grupos_db, salvar_grupos_db,
    log, garantir_campos, registrar_interacao,
    consultar_telegram_api, verificar_status_em_grupos,
    buscar_usuario, formatar_perfil, formatar_perfil_api,
    executar_varredura, executar_threads_atualizacao, auto_scanner,
    set_clients, scan_running, scan_stats, thread_scan_active,
    FILE_PATH, GROUPS_DB_PATH, SCAN_INTERVAL, THREAD_SCAN_INTERVAL,
    MAX_HISTORY, BOT_VERSION
)
from botoes import (
    menu_principal_buttons, voltar_button, perfil_buttons,
    perfil_com_api_buttons, resultado_multiplo_buttons,
    set_owner, is_admin
)
from pagina import paginar_buttons, paginar_lista, ITEMS_PER_PAGE

# ── Configurações ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SESSION_USER = os.path.join(BASE_DIR, "session_monitor")
SESSION_BOT = os.path.join(BASE_DIR, "session_bot")

BOT_CODENAME = "773H Ultra"

def carregar_token() -> str:
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("bot_token", "")
        except (json.JSONDecodeError, IOError):
            pass
    return ""

def carregar_owner_id() -> int:
    """Carrega OWNER_ID do token.json ou retorna 0."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("owner_id", 0)
        except (json.JSONDecodeError, IOError):
            pass
    return 0

BOT_TOKEN = carregar_token()
OWNER_ID = carregar_owner_id()

if not BOT_TOKEN:
    print("❌ Token não encontrado! Configure token.json")
    exit(1)

if not API_ID or not API_HASH or not PHONE:
    print("❌ Credenciais API não configuradas! Configure aplicativo.py ou aplicativo_config.json")
    exit(1)

# ── Clientes Telethon ──
user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot = TelegramClient(SESSION_BOT, API_ID, API_HASH)

# Configurar módulos
set_owner(OWNER_ID)
set_clients(bot, OWNER_ID)

# ── Estado de busca ──
search_pending = {}
tg_search_pending = {}

# ══════════════════════════════════════════════
# 🎮  HANDLERS DO BOT
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    await registrar_interacao(event)
    sender = await event.get_sender()
    uid = sender.id if sender else 0

    db = carregar_dados()
    user_info = ""
    uid_str = str(uid)
    if uid_str in db:
        d = db[uid_str]
        user_info = f"""
━━━━━━━━━━━━━━━━━━━━━
📌 **Seu Perfil no Sistema:**
├ 👤 `{d.get('nome_atual', 'N/A')}`
├ 📂 Grupos: **{len(d.get('grupos', []))}** | 👑 Admin: **{len(d.get('grupos_admin', []))}** | 🚫 Bans: **{len(d.get('grupos_banido', []))}**
├ 📝 Alterações: **{len(d.get('historico', []))}**
└ 🕐 Desde: `{d.get('primeiro_registro', 'N/A')}`"""

    await event.respond(
        f"""╔══════════════════════════════════╗
║  🕵️ **User Info Bot Pro v{BOT_VERSION}**     ║
║  _{BOT_CODENAME}_                     ║
╚══════════════════════════════════╝

🔍 **Busque** por ID, @username ou nome
🌐 **Consulte** via API Telegram
📊 **Monitore** alterações em tempo real
👑 **Descubra** grupos como admin
🚫 **Verifique** bans registrados
🧵 **Threads** atualizando em tempo real
{user_info}

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: Edivaldo Silva @Edkd1_
⚡ _Powered by {BOT_CODENAME}_
━━━━━━━━━━━━━━━━━━━━━""",
        parse_mode='md', buttons=menu_principal_buttons(uid))

@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await registrar_interacao(event)
    await cmd_start(event)

@bot.on(events.NewMessage(pattern='/id'))
async def cmd_get_id(event):
    await registrar_interacao(event)
    chat = await event.get_chat()
    sender = await event.get_sender()
    await event.reply(
        f"🔢 **IDs**\n"
        f"├ 💬 Chat: `{event.chat_id}`\n"
        f"├ 👤 Seu: `{sender.id if sender else 'N/A'}`\n"
        f"└ 📛 `{chat.title if hasattr(chat, 'title') else 'DM'}`",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'/buscar\s+(.+)'))
async def cmd_buscar_text(event):
    await registrar_interacao(event)
    query = event.pattern_match.group(1).strip()

    # 1. Busca no banco de dados local primeiro
    results = buscar_usuario(query)

    if not results:
        # 2. Se não encontrou, consulta API
        await event.reply("🔎 _Não encontrado no banco. Consultando API..._", parse_mode='md')
        dados_api = await consultar_telegram_api(user_client, query)
        if dados_api:
            uid = str(dados_api["id"])
            db = carregar_dados()
            if uid in db:
                # Verificar status em todos os grupos
                status = await verificar_status_em_grupos(user_client, dados_api["id"])
                db[uid]["grupos_admin"] = [{"grupo": g["grupo"], "cargo": g["cargo"]} for g in status["admin_em"]]
                db[uid]["grupos_banido"] = [{"grupo": g["grupo"]} for g in status["banido_de"]]
                salvar_dados(db)
                await event.reply(
                    formatar_perfil(db[uid]), parse_mode='md',
                    buttons=perfil_com_api_buttons(uid)
                )
            else:
                await event.reply(
                    formatar_perfil_api(dados_api), parse_mode='md',
                    buttons=voltar_button()
                )
            return
        await event.reply(
            "❌ **Nenhum usuário encontrado.**\n💡 Tente ID, @username ou nome.",
            parse_mode='md', buttons=voltar_button()
        )
        return

    if len(results) == 1:
        uid = str(results[0]["id"])
        await event.reply(
            formatar_perfil(results[0]), parse_mode='md',
            buttons=perfil_buttons(uid)
        )
    else:
        text = f"🔍 **{len(results)} resultados para** `{query}`:\n\n"
        await event.reply(text, parse_mode='md', buttons=resultado_multiplo_buttons(results))

# ══════════════════════════════════════════════
# 🔘  HANDLERS DE CALLBACK
# ══════════════════════════════════════════════

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    import grupo
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    try:
        message = await event.get_message()

        if data == "cmd_menu":
            await message.edit(
                f"╔══════════════════════════════════╗\n"
                f"║  🕵️ **User Info Bot Pro v{BOT_VERSION}**     ║\n"
                f"╚══════════════════════════════════╝\n\n"
                f"Selecione uma opção:",
                parse_mode='md', buttons=menu_principal_buttons(sender_id)
            )

        elif data == "cmd_buscar":
            search_pending[chat_id] = True
            await message.edit(
                "🔍 **Modo de Busca Ativo**\n\n"
                "• 🔢 **ID** — ex: `123456789`\n"
                "• 🆔 **@username** — ex: `@exemplo`\n"
                "• 📛 **Nome** — ex: `João`\n\n"
                "💡 _Busca no banco local primeiro, depois API!_\n\n"
                "_Aguardando..._",
                parse_mode='md', buttons=voltar_button()
            )

        elif data == "cmd_tg_search":
            tg_search_pending[chat_id] = True
            await message.edit(
                "🌐 **Consulta Direta — API Telegram**\n\n"
                "• 🔢 **ID numérico**\n"
                "• 🆔 **@username**\n\n"
                "⚡ _Salva automaticamente no banco_\n\n"
                "_Aguardando..._",
                parse_mode='md', buttons=voltar_button()
            )

        elif data == "cmd_stats":
            db = carregar_dados()
            groups_db = carregar_grupos_db()
            total_users = len(db)
            total_changes = sum(len(d.get("historico", [])) for d in db.values())
            total_names = sum(1 for d in db.values() for h in d.get("historico", []) if h["tipo"] == "NOME")
            total_usernames = sum(1 for d in db.values() for h in d.get("historico", []) if h["tipo"] == "USER")
            with_history = sum(1 for d in db.values() if d.get("historico"))
            total_admins = sum(1 for d in db.values() if d.get("grupos_admin"))
            total_bans = sum(len(d.get("grupos_banido", [])) for d in db.values())
            total_groups_db = len(groups_db)
            scan_possiveis = sum(1 for g in groups_db.values() if g.get("scan_possivel", False))
            last = grupo.scan_stats.get("last_scan", "Nunca")

            origens = {}
            for d in db.values():
                o = d.get("origem", "?")
                origens[o] = origens.get(o, 0) + 1
            origem_text = "".join(
                f"├ 🏷️ {o}: **{c}**\n"
                for o, c in sorted(origens.items(), key=lambda x: -x[1])
            )

            await message.edit(
                f"╔══════════════════════════════════╗\n"
                f"║  📊 **ESTATÍSTICAS COMPLETAS**     ║\n"
                f"╚══════════════════════════════════╝\n\n"
                f"👥 **Banco:** **{total_users}** usuários | **{total_groups_db}** grupos ({scan_possiveis} com scan)\n"
                f"├ 🔔 Com alterações: **{with_history}** | 👑 Admins: **{total_admins}** | 🚫 Bans: **{total_bans}**\n"
                f"└ 📊 Cobertura: **{(with_history/total_users*100) if total_users else 0:.1f}%**\n\n"
                f"📝 **Alterações:** 📛 Nomes: **{total_names}** | 🆔 Users: **{total_usernames}** | Total: **{total_changes}**\n\n"
                f"🏷️ **Origens:**\n{origem_text}\n"
                f"⚙️ Última varredura: `{last}` | Threads: **{'✅' if grupo.thread_scan_active else '❌'}**\n"
                f"🔄 Ciclo: Completa → {SCAN_INTERVAL // 60}min → Leve → {THREAD_SCAN_INTERVAL // 60}min\n"
                f"💾 Banco: **{os.path.getsize(FILE_PATH) // 1024 if os.path.exists(FILE_PATH) else 0} KB**",
                parse_mode='md', buttons=voltar_button()
            )

        elif data == "cmd_scan":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return
            if grupo.scan_running:
                await event.answer("⏳ Já em andamento!", alert=True)
            else:
                await event.answer("🔄 Varredura completa iniciada!")
                asyncio.create_task(executar_varredura(user_client, notify_chat=chat_id))

        elif data == "cmd_groups" or data.startswith("groups_page_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return
            page = int(data.split("_")[-1]) if data.startswith("groups_page_") else 0
            groups_db = carregar_grupos_db()
            all_groups = sorted(groups_db.values(), key=lambda x: x.get("nome", ""))
            chunk, page, total_pages = paginar_lista(all_groups, page)

            if not chunk:
                text = "📂 **Nenhum grupo registrado.**\nInicie uma varredura."
            else:
                text = f"📂 **Grupos Monitorados** (pág. {page + 1}/{total_pages})\n\n"
                for g in chunk:
                    icon = "✅" if g.get("scan_possivel") else "🔒"
                    text += f"{icon} **{g.get('nome', '?')}**\n   👥 {g.get('membros_coletados', 0)} | `{g.get('ultimo_scan', 'Nunca')}`\n\n"
            await message.edit(text, parse_mode='md', buttons=paginar_buttons("groups", page, total_pages))

        elif data == "cmd_threads":
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                return
            await message.edit(
                f"🧵 **Threads de Varredura Leve**\n\n"
                f"📡 Status: {'✅ ATIVAS' if grupo.thread_scan_active else '❌ PAUSADAS'}\n"
                f"⏱️ Intervalo: **{THREAD_SCAN_INTERVAL // 60} min**\n\n"
                f"_Varrem todos os grupos ligeiramente a cada ciclo._\n"
                f"_Detectam mudanças de nome, username, entradas e saídas._",
                parse_mode='md', buttons=[
                    [Button.inline(
                        "⏸️ Pausar Threads" if grupo.thread_scan_active else "▶️ Ativar Threads",
                        b"toggle_threads"
                    )],
                    [Button.inline("🔙 Menu", b"cmd_menu")]
                ]
            )

        elif data == "toggle_threads":
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                return
            grupo.thread_scan_active = not grupo.thread_scan_active
            await event.answer(
                f"Threads {'ativadas ✅' if grupo.thread_scan_active else 'pausadas ⏸️'}!",
                alert=True
            )
            await message.edit(
                f"🧵 **Threads:** {'✅ ATIVAS' if grupo.thread_scan_active else '❌ PAUSADAS'}\n\n"
                f"_Alteração aplicada com sucesso._",
                parse_mode='md', buttons=[
                    [Button.inline(
                        "⏸️ Pausar Threads" if grupo.thread_scan_active else "▶️ Ativar Threads",
                        b"toggle_threads"
                    )],
                    [Button.inline("🔙 Menu", b"cmd_menu")]
                ]
            )

        elif data == "cmd_recent" or data.startswith("recent_page_"):
            page = int(data.split("_")[-1]) if data.startswith("recent_page_") else 0
            db = carregar_dados()
            all_changes = []
            for uid, dados in db.items():
                for h in dados.get("historico", []):
                    all_changes.append({**h, "uid": uid, "nome": dados["nome_atual"]})
            all_changes.sort(key=lambda x: x["data"], reverse=True)
            chunk, page, total_pages = paginar_lista(all_changes, page)

            if not chunk:
                text = "📋 **Nenhuma alteração registrada.**"
            else:
                text = f"📋 **Últimas Alterações** (pág. {page + 1}/{total_pages})\n\n"
                for c in chunk:
                    emoji = "📛" if c["tipo"] == "NOME" else "🆔"
                    text += f"{emoji} `{c['data']}`\n   👤 {c['nome']} — {c['de']} ➜ {c['para']}\n\n"
            await message.edit(text, parse_mode='md', buttons=paginar_buttons("recent", page, total_pages))

        elif data == "cmd_export":
            if not is_admin(sender_id):
                await event.answer("🔒", alert=True)
                return
            if os.path.exists(FILE_PATH):
                await bot.send_file(
                    chat_id, FILE_PATH,
                    caption=f"📤 **Banco exportado!** 👥 {len(carregar_dados())} usuários",
                    parse_mode='md'
                )
                if os.path.exists(GROUPS_DB_PATH):
                    await bot.send_file(
                        chat_id, GROUPS_DB_PATH,
                        caption="📂 **Grupos exportado!**",
                        parse_mode='md'
                    )
                await event.answer("✅ Enviado!")
            else:
                await event.answer("❌ Banco vazio!", alert=True)

        elif data == "cmd_config":
            await message.edit(
                f"⚙️ **Configurações do Bot**\n\n"
                f"🔄 **Ciclo de Varredura:**\n"
                f"├ 📡 Completa → aguarda **{SCAN_INTERVAL // 60} min** → repete\n"
                f"├ 🧵 Leve → aguarda **{THREAD_SCAN_INTERVAL // 60} min** → repete\n"
                f"└ Threads: {'✅ Ativas' if grupo.thread_scan_active else '❌ Pausadas'}\n\n"
                f"📜 Máx hist: **{MAX_HISTORY}** | 📄 Pág: **{ITEMS_PER_PAGE}**\n"
                f"💾 `{FILE_PATH}`\n📂 `{GROUPS_DB_PATH}`",
                parse_mode='md', buttons=voltar_button()
            )

        elif data == "cmd_about":
            await message.edit(
                f"╔══════════════════════════════════╗\n"
                f"║  ℹ️ **SOBRE O BOT**                ║\n"
                f"╚══════════════════════════════════╝\n\n"
                f"🕵️ **User Info Bot Pro v{BOT_VERSION}** — _{BOT_CODENAME}_\n\n"
                f"• 🔍 Busca local + 🌐 API Telegram\n"
                f"• 📡 Varredura completa sequencial de todos os grupos\n"
                f"• 🧵 Varredura leve contínua a cada 2 minutos\n"
                f"• 👑 Detecção admins + 🚫 Registro bans\n"
                f"• 📜 Histórico paginado + 📤 Exportação\n"
                f"• 🆔 Auto-registro de usuários\n"
                f"• 🔄 Detecção de entradas/saídas de grupos\n\n"
                f"⚡ Telethon asyncio | 💾 JSON persistente | 🛡️ Anti-flood\n\n"
                f"👨‍💻 **Edivaldo Silva** @Edkd1 | v{BOT_VERSION}",
                parse_mode='md', buttons=voltar_button()
            )

        elif data.startswith("profile_"):
            uid = data.replace("profile_", "")
            db = carregar_dados()
            if uid in db:
                await message.edit(
                    formatar_perfil(db[uid]), parse_mode='md',
                    buttons=perfil_buttons(uid)
                )
            else:
                await event.answer("❌ Não encontrado.")

        elif data.startswith("apilookup_"):
            uid = data.replace("apilookup_", "")
            await event.answer("🌐 Consultando...")
            dados_api = await consultar_telegram_api(user_client, uid)
            if dados_api:
                status = await verificar_status_em_grupos(user_client, int(uid))
                db = carregar_dados()
                if uid in db:
                    db[uid]["grupos_admin"] = [{"grupo": g["grupo"], "cargo": g["cargo"]} for g in status["admin_em"]]
                    db[uid]["grupos_banido"] = [{"grupo": g["grupo"]} for g in status["banido_de"]]
                    db[uid]["dados_api"] = dados_api
                    salvar_dados(db)
                await message.edit(
                    formatar_perfil_api(dados_api), parse_mode='md',
                    buttons=[
                        [Button.inline("👤 Perfil Completo", f"profile_{uid}".encode())],
                        [Button.inline("🔙 Menu", b"cmd_menu")]
                    ]
                )
            else:
                await message.edit(
                    "❌ **Não foi possível consultar.**", parse_mode='md',
                    buttons=[
                        [Button.inline("👤 Perfil Local", f"profile_{uid}".encode())],
                        [Button.inline("🔙 Menu", b"cmd_menu")]
                    ]
                )

        elif data.startswith("apiview_"):
            uid = data.replace("apiview_", "")
            db = carregar_dados()
            if uid in db and "dados_api" in db[uid]:
                await message.edit(
                    formatar_perfil_api(db[uid]["dados_api"]), parse_mode='md',
                    buttons=[
                        [Button.inline("👤 Perfil", f"profile_{uid}".encode()),
                         Button.inline("🔄 Atualizar", f"apilookup_{uid}".encode())],
                        [Button.inline("🔙 Menu", b"cmd_menu")]
                    ]
                )
            else:
                await event.answer("Sem dados API. Use Consultar API.")

        elif data.startswith("gadmin_"):
            parts = data.split("_")
            uid, page = parts[1], int(parts[2]) if len(parts) > 2 else 0
            db = carregar_dados()
            if uid not in db:
                await event.answer("❌"); return
            lista = db[uid].get("grupos_admin", [])
            chunk, page, total_pages = paginar_lista(lista, page)
            text = f"👑 **Admin** — `{db[uid]['nome_atual']}`\nPág. {page+1}/{total_pages} | Total: **{len(lista)}**\n\n"
            for g in chunk:
                e = "👑" if g.get("cargo") == "Criador" else "🛡️"
                text += f"{e} **{g.get('grupo', '?')}** — _{g.get('cargo', 'Admin')}_\n"
            if not chunk: text += "_Nenhum._\n💡 _Use varredura ou API._"
            btns = paginar_buttons(f"gadmin_{uid}", page, total_pages)
            btns.insert(0, [Button.inline("👤 Perfil", f"profile_{uid}".encode())])
            await message.edit(text, parse_mode='md', buttons=btns)

        elif data.startswith("gban_"):
            parts = data.split("_")
            uid, page = parts[1], int(parts[2]) if len(parts) > 2 else 0
            db = carregar_dados()
            if uid not in db:
                await event.answer("❌"); return
            lista = db[uid].get("grupos_banido", [])
            chunk, page, total_pages = paginar_lista(lista, page)
            text = f"🚫 **Bans** — `{db[uid]['nome_atual']}`\nPág. {page+1}/{total_pages} | Total: **{len(lista)}**\n\n"
            for g in chunk:
                text += f"🚫 **{g.get('grupo', '?')}** — `{g.get('data', 'N/A')}`\n"
            if not chunk: text += "_Nenhum ban._"
            btns = paginar_buttons(f"gban_{uid}", page, total_pages)
            btns.insert(0, [Button.inline("👤 Perfil", f"profile_{uid}".encode())])
            await message.edit(text, parse_mode='md', buttons=btns)

        elif data.startswith("gmember_"):
            parts = data.split("_")
            uid, page = parts[1], int(parts[2]) if len(parts) > 2 else 0
            db = carregar_dados()
            if uid not in db:
                await event.answer("❌"); return
            lista = db[uid].get("grupos", [])
            chunk, page, total_pages = paginar_lista(lista, page)
            text = f"📂 **Grupos Membro** — `{db[uid]['nome_atual']}`\nPág. {page+1}/{total_pages} | Total: **{len(lista)}**\n\n"
            for g in chunk:
                text += f"📂 {g}\n"
            if not chunk: text += "_Nenhum._"
            btns = paginar_buttons(f"gmember_{uid}", page, total_pages)
            btns.insert(0, [Button.inline("👤 Perfil", f"profile_{uid}".encode())])
            await message.edit(text, parse_mode='md', buttons=btns)

        elif data.startswith("hist_"):
            parts = data.split("_")
            uid, page = parts[1], int(parts[2]) if len(parts) > 2 else 0
            db = carregar_dados()
            if uid not in db:
                await event.answer("❌"); return
            historico = list(reversed(db[uid].get("historico", [])))
            chunk, page, total_pages = paginar_lista(historico, page)
            text = f"📜 **Histórico** — `{db[uid]['nome_atual']}`\nPág. {page+1}/{total_pages} | Total: **{len(historico)}**\n\n"
            for h in chunk:
                emoji = "📛" if h.get("tipo") == "NOME" else "🆔"
                text += f"{emoji} `{h['data']}`\n   {h['de']} ➜ {h['para']}\n   📍 _{h.get('grupo', 'N/A')}_\n\n"
            if not chunk: text += "_Nenhum registro._"
            btns = paginar_buttons(f"hist_{uid}", page, total_pages)
            btns.insert(0, [Button.inline("👤 Perfil", f"profile_{uid}".encode())])
            await message.edit(text, parse_mode='md', buttons=btns)

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

# ── Texto livre ──
@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def text_handler(event):
    await registrar_interacao(event)
    chat_id = event.chat_id

    if chat_id in tg_search_pending:
        del tg_search_pending[chat_id]
        query = event.text.strip()
        await event.reply("🌐 _Consultando..._", parse_mode='md')
        dados_api = await consultar_telegram_api(user_client, query)
        if dados_api:
            uid = str(dados_api["id"])
            status = await verificar_status_em_grupos(user_client, dados_api["id"])
            db = carregar_dados()
            if uid in db:
                db[uid]["grupos_admin"] = [{"grupo": g["grupo"], "cargo": g["cargo"]} for g in status["admin_em"]]
                db[uid]["grupos_banido"] = [{"grupo": g["grupo"]} for g in status["banido_de"]]
                salvar_dados(db)
                await event.reply(
                    formatar_perfil(db[uid]), parse_mode='md',
                    buttons=[
                        [Button.inline("🌐 API", f"apiview_{uid}".encode())],
                        [Button.inline("📜 Hist", f"hist_{uid}_0".encode())],
                        [Button.inline("👑", f"gadmin_{uid}_0".encode()),
                         Button.inline("🚫", f"gban_{uid}_0".encode())],
                        [Button.inline("🔙 Menu", b"cmd_menu")]
                    ]
                )
            else:
                await event.reply(
                    formatar_perfil_api(dados_api), parse_mode='md',
                    buttons=voltar_button()
                )
        else:
            await event.reply(
                f"❌ **Não encontrado** `{query}`",
                parse_mode='md', buttons=voltar_button()
            )
        return

    if chat_id in search_pending:
        del search_pending[chat_id]
        query = event.text.strip()

        # 1. Busca banco local primeiro
        results = buscar_usuario(query)

        if not results:
            # 2. Consulta API se não encontrou
            await event.reply("🔎 _Consultando API..._", parse_mode='md')
            dados_api = await consultar_telegram_api(user_client, query)
            if dados_api:
                uid = str(dados_api["id"])
                db = carregar_dados()
                if uid in db:
                    await event.reply(
                        formatar_perfil(db[uid]), parse_mode='md',
                        buttons=[
                            [Button.inline("🌐 API", f"apiview_{uid}".encode())],
                            [Button.inline("📜 Hist", f"hist_{uid}_0".encode())],
                            [Button.inline("🔙 Menu", b"cmd_menu")]
                        ]
                    )
                else:
                    await event.reply(
                        formatar_perfil_api(dados_api), parse_mode='md',
                        buttons=voltar_button()
                    )
            else:
                await event.reply(
                    f"❌ **Nenhum resultado** `{query}`",
                    parse_mode='md', buttons=voltar_button()
                )
            return

        if len(results) == 1:
            uid = str(results[0]["id"])
            await event.reply(
                formatar_perfil(results[0]), parse_mode='md',
                buttons=perfil_buttons(uid)
            )
        else:
            text = f"🔍 **{len(results)} resultados** `{query}`:\n\n"
            await event.reply(text, parse_mode='md', buttons=resultado_multiplo_buttons(results))
    else:
        sender = await event.get_sender()
        await event.reply(
            "💡 Use o menu ou `/buscar termo`.",
            parse_mode='md',
            buttons=menu_principal_buttons(sender.id if sender else 0)
        )

# ══════════════════════════════════════════════
# 🚀  INICIALIZAÇÃO
# ══════════════════════════════════════════════

async def main():
    await user_client.start(PHONE)
    await bot.start(bot_token=BOT_TOKEN)

    log(f"🚀 ═══════════════════════════════════════")
    log(f"🚀 User Info Bot Pro v{BOT_VERSION} ({BOT_CODENAME})")
    log(f"🚀 👨‍💻 Créditos: Edivaldo Silva @Edkd1")
    log(f"🚀 ═══════════════════════════════════════")
    log(f"📡 Ciclo de varredura:")
    log(f"   1️⃣  Varredura COMPLETA — todos os grupos um por um")
    log(f"   2️⃣  Aguarda {SCAN_INTERVAL // 60} minutos")
    log(f"   3️⃣  Varredura LEVE (threads) — todos os grupos ligeiramente")
    log(f"   4️⃣  Aguarda {THREAD_SCAN_INTERVAL // 60} minutos")
    log(f"   🔁 Repete o ciclo indefinidamente")
    log(f"")
    log(f"📡 Executando primeira varredura completa...")

    # 1. Primeira varredura completa imediata — todos os grupos um por um
    await executar_varredura(user_client, notify_chat=OWNER_ID)

    # 2. Iniciar ciclos automáticos
    asyncio.create_task(auto_scanner(user_client))          # Varredura completa a cada 2 min
    asyncio.create_task(executar_threads_atualizacao(user_client))  # Varredura leve a cada 2 min

    print("✅ Bot ativo! Use /start ou /buscar")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
