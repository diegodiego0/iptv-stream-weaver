# ══════════════════════════════════════════════
# 📡  VARREDURA — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════

import asyncio
from telethon.errors import FloodWaitError

from config import DEFAULT_HIDDEN
from db import (carregar_dados, salvar_dados, log, agora_str,
                ensure_user_shape)
from profile import obter_perfil_completo, aplicar_atualizacao_campos
from notifier import notificar_mudanca_completa
from format import to_html


_scan_running = False
scan_stats    = {"last_scan": None, "users_scanned": 0,
                 "groups_scanned": 0, "changes_detected": 0}


def is_scan_running() -> bool:
    return _scan_running


async def executar_varredura(user_client, bot, notify_chat=None):
    global _scan_running, scan_stats
    if _scan_running:
        if notify_chat:
            await bot.send_message(notify_chat, "⚠️ Varredura já em andamento!")
        return
    _scan_running = True
    scan_stats = {"last_scan": None, "users_scanned": 0,
                  "groups_scanned": 0, "changes_detected": 0}
    agora = agora_str()
    scan_stats["last_scan"] = agora
    db = carregar_dados()

    if notify_chat:
        await bot.send_message(notify_chat,
            to_html("🔄 *Varredura iniciada...*\n⏳ Aguarde notificação ao finalizar."),
            parse_mode='html')

    log("🔄 Varredura iniciada")
    try:
        async for dialog in user_client.iter_dialogs():
            if not (dialog.is_group or dialog.is_channel):
                continue
            nome_grupo = dialog.name
            grupo_id   = dialog.id
            scan_stats["groups_scanned"] += 1
            try:
                async for user in user_client.iter_participants(dialog.id):
                    if user.bot:
                        continue
                    uid        = str(user.id)
                    nome_atual = (f"{user.first_name or ''} {user.last_name or ''}".strip()
                                  or "Sem nome")
                    user_atual = f"@{user.username}" if user.username else "Nenhum"
                    extras     = await obter_perfil_completo(user_client, user.id)
                    scan_stats["users_scanned"] += 1

                    if uid not in db:
                        db[uid] = {
                            "id":                user.id,
                            "nome_atual":        nome_atual,
                            "username_atual":    user_atual,
                            "bio":               extras["bio"],
                            "phone":             extras["phone"],
                            "fotos":             extras["fotos"],
                            "restricoes":        extras["restricoes"],
                            "grupos":            [nome_grupo],
                            "grupos_ids":        [grupo_id],
                            "fonte":             "Varredura",
                            "primeiro_registro": agora,
                            "historico":         [],
                            "hidden_info":       dict(DEFAULT_HIDDEN),
                            "premium":           {"active": False, "modules": []},
                            "custom_combo_limits": {},
                        }
                    else:
                        ensure_user_shape(db[uid])
                        if nome_grupo not in db[uid].get("grupos", []):
                            db[uid].setdefault("grupos", []).append(nome_grupo)
                        if grupo_id not in db[uid].get("grupos_ids", []):
                            db[uid].setdefault("grupos_ids", []).append(grupo_id)

                        mudancas = aplicar_atualizacao_campos(
                            db[uid],
                            nome=nome_atual, username=user_atual,
                            bio=extras["bio"], phone=extras["phone"],
                            grupo=nome_grupo,
                        )
                        if mudancas:
                            scan_stats["changes_detected"] += len(mudancas)
                            # Salva ANTES de notificar para o perfil refletir o estado novo
                            salvar_dados(db)
                            await notificar_mudanca_completa(
                                bot, uid, mudancas, grupo=nome_grupo
                            )
                        db[uid]["fotos"]      = extras["fotos"]
                        db[uid]["restricoes"] = extras["restricoes"]

            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                log(f"⚠️ Erro grupo {nome_grupo}: {e}")
    except Exception as e:
        log(f"❌ Varredura: {e}")
    finally:
        salvar_dados(db)
        _scan_running = False
        log(f"✅ Varredura: {scan_stats['groups_scanned']} grupos / "
            f"{scan_stats['users_scanned']} usuários / "
            f"{scan_stats['changes_detected']} alterações")

    if notify_chat:
        from ui import voltar_button
        from lang import t
        await bot.send_message(
            notify_chat,
            to_html(t("scan_done", notify_chat,
              g=scan_stats['groups_scanned'],
              u=scan_stats['users_scanned'],
              c=scan_stats['changes_detected'],
              ts=agora)),
            parse_mode='html', buttons=voltar_button(notify_chat)
        )
