# ══════════════════════════════════════════════
# 📡  FUNÇÕES DE GRUPO — INFO BOT PRO V4.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════

import os
import json
import asyncio
from datetime import datetime
from telethon.errors import FloodWaitError, UserNotParticipantError, ChatAdminRequiredError, ChannelPrivateError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import (
    ChannelParticipantAdmin, ChannelParticipantCreator,
    ChannelParticipantBanned
)

# ── Caminhos ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "banco_de_dados.json")
GROUPS_DB_PATH = os.path.join(BASE_DIR, "groups_database.json")
LOG_PATH = os.path.join(BASE_DIR, "monitor.log")

MAX_HISTORY = 50
SCAN_INTERVAL = 120         # 2 minutos — intervalo entre ciclos completos
THREAD_SCAN_INTERVAL = 120  # 2 minutos — threads contínuas

BOT_VERSION = "4.0"

# ── Estado global ──
scan_running = False
scan_stats = {"last_scan": None, "users_scanned": 0, "groups_scanned": 0, "changes_detected": 0}
thread_scan_active = True

# ══════════════════════════════════════════════
# 📁  BANCO DE DADOS JSON
# ══════════════════════════════════════════════

def carregar_dados() -> dict:
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def salvar_dados(db: dict):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar banco: {e}")

def carregar_grupos_db() -> dict:
    if os.path.exists(GROUPS_DB_PATH):
        try:
            with open(GROUPS_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def salvar_grupos_db(db: dict):
    try:
        with open(GROUPS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar banco de grupos: {e}")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except IOError:
        pass

def garantir_campos(db, uid):
    """Garante que campos novos existam no registro."""
    for campo, default in [("grupos_admin", []), ("grupos_banido", []),
                           ("ultimo_visto", ""), ("grupos", []),
                           ("grupos_historico", [])]:
        if campo not in db[uid]:
            db[uid][campo] = default

# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════

_bot_client = None
_owner_id = 0

def set_clients(bot_client, owner_id: int):
    global _bot_client, _owner_id
    _bot_client = bot_client
    _owner_id = owner_id

async def notificar(texto: str):
    try:
        if _bot_client:
            await _bot_client.send_message(_owner_id, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")

# ══════════════════════════════════════════════
# 👤  REGISTRO DE INTERAÇÃO
# ══════════════════════════════════════════════

async def registrar_interacao(event):
    """Registra qualquer interação de usuário com o bot."""
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
                "id": user.id, "nome_atual": nome, "username_atual": username,
                "grupos": [], "grupos_admin": [], "grupos_banido": [],
                "grupos_historico": [],
                "primeiro_registro": agora, "historico": [],
                "origem": "interacao_bot", "ultimo_visto": agora
            }
            salvar_dados(db)
            log(f"➕ Novo usuário registrado via interação: {nome} ({uid})")
        else:
            changed = False
            db[uid]["ultimo_visto"] = agora
            garantir_campos(db, uid)
            if db[uid]["nome_atual"] != nome:
                db[uid]["historico"].append({
                    "data": agora, "tipo": "NOME",
                    "de": db[uid]["nome_atual"], "para": nome, "grupo": "Bot DM"
                })
                db[uid]["nome_atual"] = nome
                changed = True
            if db[uid]["username_atual"] != username:
                db[uid]["historico"].append({
                    "data": agora, "tipo": "USER",
                    "de": db[uid]["username_atual"], "para": username, "grupo": "Bot DM"
                })
                db[uid]["username_atual"] = username
                changed = True
            if changed and len(db[uid]["historico"]) > MAX_HISTORY:
                db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]
            salvar_dados(db)
    except Exception as e:
        log(f"⚠️ Erro ao registrar interação: {e}")

# ══════════════════════════════════════════════
# 🌐  CONSULTA VIA API TELEGRAM
# ══════════════════════════════════════════════

async def consultar_telegram_api(user_client, query: str) -> dict:
    """Consulta a API do Telegram por ID ou username."""
    try:
        if query.isdigit():
            entity = await user_client.get_entity(int(query))
        else:
            entity = await user_client.get_entity(query)

        if not entity:
            return None

        full_user = None
        try:
            full_user = await user_client(GetFullUserRequest(entity.id))
        except Exception:
            pass

        nome = f"{entity.first_name or ''} {entity.last_name or ''}".strip() or "Sem nome"
        username = f"@{entity.username}" if entity.username else "Nenhum"
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        dados_api = {
            "id": entity.id, "nome": nome, "username": username,
            "telefone": entity.phone if hasattr(entity, 'phone') and entity.phone else "Oculto",
            "bot": getattr(entity, 'bot', False),
            "verificado": getattr(entity, 'verified', False),
            "restrito": getattr(entity, 'restricted', False),
            "premium": getattr(entity, 'premium', False),
            "foto_perfil": bool(entity.photo) if hasattr(entity, 'photo') else False,
            "bio": "", "consultado_em": agora
        }

        if full_user and hasattr(full_user, 'full_user'):
            dados_api["bio"] = full_user.full_user.about or ""

        # Salva/atualiza no banco
        db = carregar_dados()
        uid = str(entity.id)
        if uid not in db:
            db[uid] = {
                "id": entity.id, "nome_atual": nome, "username_atual": username,
                "grupos": [], "grupos_admin": [], "grupos_banido": [],
                "grupos_historico": [],
                "primeiro_registro": agora, "historico": [],
                "origem": "consulta_api", "ultimo_visto": agora, "dados_api": dados_api
            }
            log(f"➕ Novo usuário via API Telegram: {nome} ({uid})")
        else:
            db[uid]["dados_api"] = dados_api
            db[uid]["ultimo_visto"] = agora
            garantir_campos(db, uid)
        salvar_dados(db)
        return dados_api
    except Exception as e:
        log(f"⚠️ Erro consulta API Telegram: {e}")
        return None

async def verificar_status_em_grupos(user_client, user_id: int) -> dict:
    """Verifica globalmente em quais grupos o usuário está, é admin ou banido."""
    resultado = {"admin_em": [], "banido_de": [], "membro_de": []}
    try:
        async for dialog in user_client.iter_dialogs():
            if not (dialog.is_group or dialog.is_channel):
                continue
            try:
                participant = await user_client(GetParticipantRequest(
                    channel=dialog.id, participant=user_id
                ))
                p = participant.participant
                if isinstance(p, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                    cargo = "Criador" if isinstance(p, ChannelParticipantCreator) else "Admin"
                    resultado["admin_em"].append({"grupo": dialog.name, "cargo": cargo})
                elif isinstance(p, ChannelParticipantBanned):
                    resultado["banido_de"].append({"grupo": dialog.name})
                else:
                    resultado["membro_de"].append(dialog.name)
            except UserNotParticipantError:
                # Usuário não está mais neste grupo — registrar saída
                continue
            except (ChatAdminRequiredError, ChannelPrivateError):
                continue
            except FloodWaitError as e:
                log(f"⏳ FloodWait verificação: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception:
                continue
    except Exception as e:
        log(f"⚠️ Erro ao verificar status em grupos: {e}")
    return resultado

# ══════════════════════════════════════════════
# 🔍  BUSCA AVANÇADA
# ══════════════════════════════════════════════

def buscar_usuario(query: str) -> list:
    """Busca precisa por ID, username ou nome no banco local."""
    db = carregar_dados()
    query_lower = query.lower().lstrip('@')
    results = []
    for uid, dados in db.items():
        # Busca exata por ID
        if query == uid:
            results.insert(0, dados)
            continue
        # Busca exata por username
        username = dados.get("username_atual", "").lower().lstrip('@')
        if username and query_lower == username:
            results.insert(0, dados)
            continue
        # Busca parcial por nome
        nome = dados.get("nome_atual", "").lower()
        if query_lower in nome or query_lower in username:
            results.append(dados)
    return results

# ══════════════════════════════════════════════
# 🎨  FORMATAÇÃO DE PERFIL
# ══════════════════════════════════════════════

def formatar_perfil(dados: dict) -> str:
    uid = dados.get("id", "?")
    nome = dados.get("nome_atual", "Desconhecido")
    username = dados.get("username_atual", "Nenhum")
    historico = dados.get("historico", [])
    total_changes = len(historico)
    grupos = dados.get("grupos", [])
    grupos_admin = dados.get("grupos_admin", [])
    grupos_banido = dados.get("grupos_banido", [])
    grupos_historico = dados.get("grupos_historico", [])
    origem = dados.get("origem", "desconhecida")
    ultimo_visto = dados.get("ultimo_visto", "N/A")
    dados_api = dados.get("dados_api", {})

    recent = historico[-5:]
    hist_text = ""
    for h in reversed(recent):
        emoji = "📛" if h.get("tipo") == "NOME" else "🆔" if h.get("tipo") == "USER" else "📂"
        hist_text += f"  {emoji} `{h['data']}` — {h['de']} ➜ {h['para']}\n"
    if not hist_text:
        hist_text = "  _Nenhuma alteração registrada_\n"

    first_seen = dados.get("primeiro_registro", "N/A")
    last_change = historico[-1]["data"] if historico else "N/A"

    badges = ""
    if dados_api.get("premium"): badges += "⭐ "
    if dados_api.get("verificado"): badges += "✅ "
    if dados_api.get("bot"): badges += "🤖 "

    admin_text = ""
    if grupos_admin:
        for g in grupos_admin[:5]:
            cargo = g.get("cargo", "Admin")
            e = "👑" if cargo == "Criador" else "🛡️"
            admin_text += f"  {e} {g.get('grupo', '?')} ({cargo})\n"
        if len(grupos_admin) > 5:
            admin_text += f"  _...e mais {len(grupos_admin) - 5}_\n"
    else:
        admin_text = "  _Nenhum grupo como admin_\n"

    ban_text = ""
    if grupos_banido:
        for g in grupos_banido[:5]:
            ban_text += f"  🚫 {g.get('grupo', '?')}\n"
        if len(grupos_banido) > 5:
            ban_text += f"  _...e mais {len(grupos_banido) - 5}_\n"
    else:
        ban_text = "  _Nenhum ban registrado_\n"

    # Histórico de grupos (entrou/saiu)
    grp_hist_text = ""
    if grupos_historico:
        for gh in grupos_historico[-5:]:
            icon = "🟢" if gh.get("acao") == "ENTROU" else "🔴"
            grp_hist_text += f"  {icon} `{gh['data']}` — {gh['grupo']} ({gh['acao']})\n"
    if not grp_hist_text:
        grp_hist_text = "  _Sem movimentações_\n"

    bio_text = dados_api.get("bio", "") if dados_api else ""
    bio_line = f"\n📝 **Bio:** _{bio_text}_" if bio_text else ""

    return f"""╔══════════════════════════════╗
║  🕵️ **PERFIL DO USUÁRIO** {badges}   ║
╚══════════════════════════════╝

👤 **Nome:** `{nome}`
🆔 **Username:** `{username}`
🔢 **ID:** `{uid}`{bio_line}
🏷️ **Origem:** `{origem}`
🕐 **Último visto:** `{ultimo_visto}`

📊 **Resumo:**
├ 📝 Total de alterações: **{total_changes}**
├ 📅 Primeiro registro: `{first_seen}`
├ 🕐 Última alteração: `{last_change}`
├ 📂 Grupos atuais: **{len(grupos)}**
├ 👑 Admin em: **{len(grupos_admin)}**
└ 🚫 Banido de: **{len(grupos_banido)}**

👑 **Admin em:**
{admin_text}
🚫 **Banido de:**
{ban_text}
📜 **Últimas Alterações:**
{hist_text}
🔄 **Movimentações em Grupos:**
{grp_hist_text}
━━━━━━━━━━━━━━━━━━━━━
_👨‍💻 @Edkd1 | v{BOT_VERSION}_"""

def formatar_perfil_api(dados_api: dict) -> str:
    badges = ""
    if dados_api.get("premium"): badges += "⭐ Premium "
    if dados_api.get("verificado"): badges += "✅ Verificado "
    if dados_api.get("bot"): badges += "🤖 Bot "

    bio = dados_api.get("bio", "")
    bio_line = f"\n📝 **Bio:** _{bio}_" if bio else ""

    return f"""╔══════════════════════════════╗
║  🌐 **CONSULTA TELEGRAM API**  ║
╚══════════════════════════════╝

👤 **Nome:** `{dados_api.get('nome', '?')}`
🆔 **Username:** `{dados_api.get('username', 'Nenhum')}`
🔢 **ID:** `{dados_api.get('id', '?')}`
📞 **Telefone:** `{dados_api.get('telefone', 'Oculto')}`{bio_line}

🏷️ **Badges:** {badges if badges else '_Nenhum_'}
📸 **Foto:** {'✅' if dados_api.get('foto_perfil') else '❌'}
🔒 **Restrito:** {'⚠️ Sim' if dados_api.get('restrito') else '✅ Não'}

🕐 **Consultado:** `{dados_api.get('consultado_em', 'N/A')}`

━━━━━━━━━━━━━━━━━━━━━
_👨‍💻 @Edkd1 | v{BOT_VERSION}_"""

# ══════════════════════════════════════════════
# 📡  VARREDURA DE GRUPOS
# ══════════════════════════════════════════════

async def executar_varredura(user_client, notify_chat=None):
    """Varredura completa de todos os grupos — um por um sequencialmente."""
    global scan_running, scan_stats
    if scan_running:
        if notify_chat and _bot_client:
            await _bot_client.send_message(notify_chat, "⚠️ Uma varredura já está em andamento!")
        return

    scan_running = True
    scan_stats = {"last_scan": None, "users_scanned": 0, "groups_scanned": 0, "changes_detected": 0}
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    scan_stats["last_scan"] = agora
    db = carregar_dados()
    groups_db = carregar_grupos_db()

    if notify_chat and _bot_client:
        await _bot_client.send_message(
            notify_chat,
            "🔄 **Varredura Completa Iniciada**\n\n"
            "⏳ Varrendo todos os grupos sequencialmente, um por um.\n"
            "📡 Você será notificado ao finalizar.",
            parse_mode='md'
        )

    log("🔄 ═══ VARREDURA COMPLETA INICIADA ═══")
    log("📡 Modo: sequencial — todos os grupos um por um")

    # Rastrear membros atuais de cada grupo para detectar saídas
    membros_atuais_por_grupo = {}

    try:
        # Coletar todos os diálogos primeiro para mostrar progresso
        dialogs_lista = []
        async for dialog in user_client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                dialogs_lista.append(dialog)

        total_dialogs = len(dialogs_lista)
        log(f"📂 Total de grupos/canais encontrados: {total_dialogs}")

        if notify_chat and _bot_client:
            await _bot_client.send_message(
                notify_chat,
                f"📂 **{total_dialogs} grupos** encontrados.\n"
                f"🔍 Iniciando varredura sequencial...",
                parse_mode='md'
            )

        # Varrer cada grupo sequencialmente — um por um
        for idx, dialog in enumerate(dialogs_lista, 1):
            nome_grupo = dialog.name
            gid = str(dialog.id)
            scan_stats["groups_scanned"] += 1
            log(f"📂 [{idx}/{total_dialogs}] Varrendo: {nome_grupo}")

            if gid not in groups_db:
                groups_db[gid] = {
                    "id": dialog.id, "nome": nome_grupo,
                    "tipo": "grupo" if dialog.is_group else "canal",
                    "primeiro_scan": agora, "ultimo_scan": agora,
                    "membros_coletados": 0, "scan_possivel": True
                }
            else:
                groups_db[gid]["nome"] = nome_grupo
                groups_db[gid]["ultimo_scan"] = agora

            try:
                membros_count = 0
                membros_ids_atuais = set()

                async for user in user_client.iter_participants(dialog.id):
                    if user.bot:
                        continue

                    uid = str(user.id)
                    nome_atual = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome"
                    user_atual = f"@{user.username}" if user.username else "Nenhum"
                    scan_stats["users_scanned"] += 1
                    membros_count += 1
                    membros_ids_atuais.add(uid)

                    if uid not in db:
                        db[uid] = {
                            "id": user.id, "nome_atual": nome_atual,
                            "username_atual": user_atual,
                            "grupos": [nome_grupo], "grupos_admin": [],
                            "grupos_banido": [], "grupos_historico": [],
                            "primeiro_registro": agora, "historico": [],
                            "origem": "varredura", "ultimo_visto": agora
                        }
                    else:
                        db[uid]["ultimo_visto"] = agora
                        garantir_campos(db, uid)

                        # Registrar entrada no grupo se novo
                        if nome_grupo not in db[uid]["grupos"]:
                            db[uid]["grupos"].append(nome_grupo)
                            db[uid]["grupos_historico"].append({
                                "data": agora, "acao": "ENTROU",
                                "grupo": nome_grupo
                            })

                        # Detectar mudança de nome
                        if db[uid]["nome_atual"] != nome_atual:
                            scan_stats["changes_detected"] += 1
                            db[uid]["historico"].append({
                                "data": agora, "tipo": "NOME",
                                "de": db[uid]["nome_atual"], "para": nome_atual,
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

                        # Detectar mudança de username
                        if db[uid]["username_atual"] != user_atual:
                            scan_stats["changes_detected"] += 1
                            db[uid]["historico"].append({
                                "data": agora, "tipo": "USER",
                                "de": db[uid]["username_atual"], "para": user_atual,
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

                        if len(db[uid]["historico"]) > MAX_HISTORY:
                            db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]

                    # Verifica admin/ban
                    try:
                        participant = await user_client(GetParticipantRequest(
                            channel=dialog.id, participant=user.id
                        ))
                        p = participant.participant
                        if isinstance(p, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                            cargo = "Criador" if isinstance(p, ChannelParticipantCreator) else "Admin"
                            db[uid]["grupos_admin"] = [
                                g for g in db[uid].get("grupos_admin", [])
                                if g.get("grupo") != nome_grupo
                            ]
                            db[uid]["grupos_admin"].append({"grupo": nome_grupo, "cargo": cargo})
                        elif isinstance(p, ChannelParticipantBanned):
                            existing = [g.get("grupo") for g in db[uid].get("grupos_banido", [])]
                            if nome_grupo not in existing:
                                db[uid]["grupos_banido"].append({"grupo": nome_grupo, "data": agora})
                    except Exception:
                        pass

                groups_db[gid]["membros_coletados"] = membros_count
                groups_db[gid]["scan_possivel"] = True

                # Detectar saídas — usuários que estavam no grupo mas não estão mais
                for uid_db, dados_db in db.items():
                    garantir_campos(db, uid_db)
                    if nome_grupo in dados_db["grupos"] and uid_db not in membros_ids_atuais:
                        dados_db["grupos"].remove(nome_grupo)
                        dados_db["grupos_historico"].append({
                            "data": agora, "acao": "SAIU/EXPULSO",
                            "grupo": nome_grupo
                        })
                        scan_stats["changes_detected"] += 1
                        await notificar(
                            f"🔴 **SAÍDA DE GRUPO**\n\n"
                            f"👤 `{dados_db['nome_atual']}` (`{uid_db}`)\n"
                            f"📍 Grupo: _{nome_grupo}_\n"
                            f"_Saiu ou foi expulso/banido_"
                        )

                log(f"  ✅ {nome_grupo}: {membros_count} membros coletados")

            except FloodWaitError as e:
                log(f"⏳ FloodWait: aguardando {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except (ChatAdminRequiredError, ChannelPrivateError):
                groups_db[gid]["scan_possivel"] = False
                log(f"  🔒 {nome_grupo}: sem permissão")
                continue
            except Exception as e:
                log(f"⚠️ Erro no grupo {nome_grupo}: {e}")
                continue

            # Salvar progresso a cada grupo (resiliência)
            salvar_dados(db)
            salvar_grupos_db(groups_db)

            # Pausa anti-flood entre grupos
            await asyncio.sleep(1)

    except Exception as e:
        log(f"❌ Erro na varredura: {e}")
    finally:
        salvar_dados(db)
        salvar_grupos_db(groups_db)
        scan_running = False
        log(f"✅ ═══ VARREDURA COMPLETA CONCLUÍDA ═══")
        log(f"   📂 Grupos: {scan_stats['groups_scanned']} | "
            f"👥 Usuários: {scan_stats['users_scanned']} | "
            f"🔔 Alterações: {scan_stats['changes_detected']}")

    if notify_chat and _bot_client:
        from botoes import voltar_button
        await _bot_client.send_message(
            notify_chat,
            f"✅ **Varredura Completa Concluída!**\n\n"
            f"📂 Grupos varridos: **{scan_stats['groups_scanned']}**\n"
            f"👥 Usuários analisados: **{scan_stats['users_scanned']}**\n"
            f"🔔 Alterações detectadas: **{scan_stats['changes_detected']}**\n"
            f"🕐 `{agora}`\n\n"
            f"⏱️ _Próxima varredura em {SCAN_INTERVAL // 60} minutos..._",
            parse_mode='md', buttons=voltar_button()
        )

# ══════════════════════════════════════════════
# 🧵  THREADS DE ATUALIZAÇÃO CONTÍNUA (LEVE)
# ══════════════════════════════════════════════

async def thread_atualizar_grupo(user_client, dialog):
    """Atualiza um grupo individual — varredura leve."""
    gid = str(dialog.id)
    nome_grupo = dialog.name
    db = carregar_dados()
    groups_db = carregar_grupos_db()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    changes = 0

    if gid not in groups_db:
        groups_db[gid] = {
            "id": dialog.id, "nome": nome_grupo,
            "tipo": "grupo" if dialog.is_group else "canal",
            "primeiro_scan": agora, "ultimo_scan": agora,
            "membros_coletados": 0, "scan_possivel": True
        }
    else:
        groups_db[gid]["ultimo_scan"] = agora
        groups_db[gid]["nome"] = nome_grupo

    try:
        membros_count = 0
        membros_ids = set()

        async for user in user_client.iter_participants(dialog.id):
            if user.bot:
                continue
            uid = str(user.id)
            nome_atual = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sem nome"
            user_atual = f"@{user.username}" if user.username else "Nenhum"
            membros_count += 1
            membros_ids.add(uid)

            if uid not in db:
                db[uid] = {
                    "id": user.id, "nome_atual": nome_atual,
                    "username_atual": user_atual,
                    "grupos": [nome_grupo], "grupos_admin": [],
                    "grupos_banido": [], "grupos_historico": [{
                        "data": agora, "acao": "ENTROU", "grupo": nome_grupo
                    }],
                    "primeiro_registro": agora, "historico": [],
                    "origem": "thread_scan", "ultimo_visto": agora
                }
                changes += 1
            else:
                db[uid]["ultimo_visto"] = agora
                garantir_campos(db, uid)
                if nome_grupo not in db[uid]["grupos"]:
                    db[uid]["grupos"].append(nome_grupo)
                    db[uid]["grupos_historico"].append({
                        "data": agora, "acao": "ENTROU", "grupo": nome_grupo
                    })
                if db[uid]["nome_atual"] != nome_atual:
                    changes += 1
                    db[uid]["historico"].append({
                        "data": agora, "tipo": "NOME",
                        "de": db[uid]["nome_atual"], "para": nome_atual,
                        "grupo": nome_grupo
                    })
                    db[uid]["nome_atual"] = nome_atual
                if db[uid]["username_atual"] != user_atual:
                    changes += 1
                    db[uid]["historico"].append({
                        "data": agora, "tipo": "USER",
                        "de": db[uid]["username_atual"], "para": user_atual,
                        "grupo": nome_grupo
                    })
                    db[uid]["username_atual"] = user_atual
                if len(db[uid]["historico"]) > MAX_HISTORY:
                    db[uid]["historico"] = db[uid]["historico"][-MAX_HISTORY:]

        # Detectar saídas
        for uid_db, dados_db in db.items():
            garantir_campos(db, uid_db)
            if nome_grupo in dados_db["grupos"] and uid_db not in membros_ids:
                dados_db["grupos"].remove(nome_grupo)
                dados_db["grupos_historico"].append({
                    "data": agora, "acao": "SAIU/EXPULSO", "grupo": nome_grupo
                })
                changes += 1

        groups_db[gid]["membros_coletados"] = membros_count
        groups_db[gid]["scan_possivel"] = True
    except (ChatAdminRequiredError, ChannelPrivateError):
        groups_db[gid]["scan_possivel"] = False
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception as e:
        log(f"⚠️ Thread erro em {nome_grupo}: {e}")

    salvar_dados(db)
    salvar_grupos_db(groups_db)
    return changes

async def executar_threads_atualizacao(user_client):
    """Loop contínuo — varredura leve de todos os grupos a cada 2 minutos."""
    global thread_scan_active
    while True:
        if not thread_scan_active:
            await asyncio.sleep(30)
            continue

        log("🧵 ═══ VARREDURA LEVE INICIADA ═══")
        log("📡 Modo: threads — varrendo todos os grupos ligeiramente")
        total_changes = 0
        total_groups = 0

        try:
            # Coletar todos os diálogos
            dialogs_lista = []
            async for dialog in user_client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    dialogs_lista.append(dialog)

            total_encontrados = len(dialogs_lista)
            log(f"📂 {total_encontrados} grupos encontrados para varredura leve")

            # Varrer todos os grupos sequencialmente (leve)
            for idx, dialog in enumerate(dialogs_lista, 1):
                if not thread_scan_active:
                    log("⏸️ Threads pausadas pelo administrador")
                    break

                total_groups += 1
                try:
                    changes = await thread_atualizar_grupo(user_client, dialog)
                    total_changes += changes
                    if changes > 0:
                        log(f"  🔔 [{idx}/{total_encontrados}] {dialog.name}: {changes} alterações")
                except Exception as e:
                    log(f"⚠️ Thread falhou para {dialog.name}: {e}")

                await asyncio.sleep(2)  # Anti-flood entre grupos

        except Exception as e:
            log(f"❌ Erro nas threads: {e}")

        log(f"🧵 ═══ VARREDURA LEVE CONCLUÍDA ═══")
        log(f"   📂 Grupos: {total_groups} | 🔔 Alterações: {total_changes}")
        log(f"   ⏱️ Próxima varredura leve em {THREAD_SCAN_INTERVAL // 60} minutos...")

        # Aguardar 2 minutos antes da próxima varredura leve
        await asyncio.sleep(THREAD_SCAN_INTERVAL)

# ══════════════════════════════════════════════
# 🔁  VARREDURA AUTOMÁTICA CÍCLICA
# ══════════════════════════════════════════════

async def auto_scanner(user_client):
    """Ciclo automático: varredura completa → aguardar 2 min → repetir."""
    while True:
        log(f"⏱️ Aguardando {SCAN_INTERVAL // 60} minutos para próxima varredura completa...")
        await asyncio.sleep(SCAN_INTERVAL)
        log("🔄 Varredura automática completa iniciada")
        await executar_varredura(user_client)
