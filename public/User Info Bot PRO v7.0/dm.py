# ══════════════════════════════════════════════
# 💬  DM — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Salva/atualiza usuários que iniciam conversa em DM com o bot.
"""

import asyncio
from config import DEFAULT_HIDDEN
from db import (carregar_dados, salvar_dados, log, agora_str,
                ensure_user_shape)
from profile import obter_perfil_completo, aplicar_atualizacao_campos
from notifier import notificar_simples, notificar_mudanca_completa


async def salvar_usuario_dm(bot, user) -> None:
    db    = carregar_dados()
    uid   = str(user.id)
    nome_atual = (f"{user.first_name or ''} {user.last_name or ''}".strip()
                  or "Sem nome")
    user_atual = f"@{user.username}" if user.username else "Nenhum"
    extras     = await obter_perfil_completo(bot, user.id)

    if uid not in db:
        db[uid] = {
            "id":                user.id,
            "nome_atual":        nome_atual,
            "username_atual":    user_atual,
            "bio":               extras["bio"],
            "phone":             extras["phone"],
            "fotos":             extras["fotos"],
            "restricoes":        extras["restricoes"],
            "grupos":            [], "grupos_ids": [],
            "fonte":             "DM",
            "primeiro_registro": agora_str(),
            "historico":         [],
            "hidden_info":       dict(DEFAULT_HIDDEN),
            "premium":           {"active": False, "modules": []},
            "custom_combo_limits": {},
        }
        salvar_dados(db)
        log(f"💬 Novo via DM: {nome_atual} ({uid})")
        await notificar_simples(
            bot,
            f"💬 *NOVO USUÁRIO (DM)*\n👤 `{nome_atual}`\n🆔 `{uid}`\n{user_atual}"
        )
        return

    ensure_user_shape(db[uid])
    mudancas = aplicar_atualizacao_campos(
        db[uid],
        nome=nome_atual, username=user_atual,
        bio=extras["bio"], phone=extras["phone"],
        grupo="DM",
    )
    db[uid]["fotos"]      = extras["fotos"]
    db[uid]["restricoes"] = extras["restricoes"]
    salvar_dados(db)
    if mudancas:
        await notificar_mudanca_completa(bot, uid, mudancas, grupo="DM")
