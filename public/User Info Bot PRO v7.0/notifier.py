# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÕES — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Notifica o owner. Quando há mudança em qualquer perfil, envia
o PERFIL COMPLETO do usuário alvo (não apenas o diff).
"""

from config import OWNER_ID
from db import log, carregar_dados
from profile import formatar_perfil
from ui import perfil_link_buttons
from format import to_html


async def notificar_simples(bot, texto: str):
    try:
        await bot.send_message(OWNER_ID, to_html(texto), parse_mode='html')
    except Exception as e:
        log(f"Erro notificação: {e}")


async def notificar_mudanca_completa(bot, uid: str, mudancas: list,
                                      grupo: str = "N/A"):
    """
    Envia o perfil COMPLETO do usuário alterado, com cabeçalho listando
    o que mudou. Apaga ruído de múltiplas notifs separadas.
    """
    if not mudancas:
        return
    db = carregar_dados()
    if uid not in db:
        return
    label = {"NOME": "📛 NOME", "USER": "🆔 USERNAME",
             "BIO": "📝 BIO", "PHONE": "📱 TELEFONE"}
    linhas = []
    for tipo, de, para in mudancas:
        tag = label.get(tipo, tipo)
        linhas.append(f"• {tag}: `{de}` ➜ `{para}`")
    cabecalho = (
        "🔔 *PERFIL ATUALIZADO*\n"
        f"📍 _Detectado em: {grupo}_\n\n"
        + "\n".join(linhas) + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    perfil = formatar_perfil(uid, db[uid], OWNER_ID, db)
    try:
        await bot.send_message(
            OWNER_ID,
            to_html(cabecalho + perfil),
            parse_mode='html',
            buttons=perfil_link_buttons(db[uid]) or None,
            link_preview=False,
        )
    except Exception as e:
        log(f"Erro notificar_mudanca_completa: {e}")
