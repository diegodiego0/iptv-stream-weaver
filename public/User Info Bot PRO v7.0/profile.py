# ══════════════════════════════════════════════
# 🧬  PERFIL — captura/atualização/formatação
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════

import re
from telethon.tl.functions.users import GetFullUserRequest
from db import log, agora_str, ensure_user_shape


# ── Censura de telefone ──
def censurar_telefone(phone: str) -> str:
    if not phone:
        return "_Não disponível_"
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 2:
        return "`+**`"
    keep = max(1, len(digits) // 5)
    vis  = digits[:keep]
    mask = '*' * (len(digits) - keep)
    prefix = '+' if phone.startswith('+') else ''
    return f"`{prefix}{vis}{mask}`"


def exibir_telefone(dados: dict, viewer_id: int, db: dict) -> str:
    from access import is_owner, has_module, is_field_hidden
    phone  = dados.get("phone", "")
    hidden = is_field_hidden(dados, "phone")
    uid    = str(viewer_id)
    if is_owner(viewer_id):
        tag = " _(oculto para outros)_" if hidden else ""
        return f"`{phone}`{tag}" if phone else f"_Não disponível_{tag}"
    if hidden:
        return "🔒 _Oculto pelo administrador_"
    if has_module(db, uid, "phone_full"):
        return f"`{phone}`" if phone else "_Não disponível_"
    return censurar_telefone(phone)


# ── Captura completa via Telethon ──
async def obter_perfil_completo(client, user_id) -> dict:
    """Retorna dict { bio, phone, fotos, restricoes }."""
    extras = {"bio": "", "phone": "", "fotos": False, "restricoes": "Nenhuma"}
    try:
        full = await client(GetFullUserRequest(user_id))
        extras["bio"] = (getattr(full.full_user, 'about', '') or "").strip()
        try:
            photos = await client.get_profile_photos(user_id, limit=1)
            extras["fotos"] = len(photos) > 0
        except Exception:
            pass
        raw_user = full.users[0] if full.users else None
        if raw_user:
            extras["phone"]      = getattr(raw_user, 'phone', '') or ""
            extras["restricoes"] = str(getattr(raw_user, 'restriction_reason', '') or "Nenhuma")
    except Exception as e:
        log(f"⚠️ Perfil completo indisponível para {user_id}: {e}")
    return extras


# ── Aplicação de mudanças com histórico ──
def aplicar_atualizacao_campos(entry: dict, *, nome=None, username=None,
                                bio=None, phone=None, grupo="N/A") -> list:
    """
    Atualiza nome/username/bio/phone, registra no histórico, retorna lista
    de tuplas (TIPO, antigo, novo) para uso em notificações.
    """
    from config import MAX_HISTORY
    ensure_user_shape(entry)
    mudancas = []
    ts = agora_str()
    historico = entry.setdefault("historico", [])

    def _push(tipo, de, para):
        historico.append({"tipo": tipo, "de": de, "para": para,
                          "data": ts, "grupo": grupo})
        mudancas.append((tipo, de, para))

    if nome is not None and nome != entry.get("nome_atual"):
        _push("NOME", entry.get("nome_atual", "?"), nome)
        entry["nome_atual"] = nome
    if username is not None and username != entry.get("username_atual"):
        _push("USER", entry.get("username_atual", "?"), username)
        entry["username_atual"] = username
    if bio is not None and bio != entry.get("bio", ""):
        _push("BIO", (entry.get("bio") or "_(vazio)_")[:60],
              (bio or "_(vazio)_")[:60])
        entry["bio"] = bio
    if phone is not None and phone != entry.get("phone", ""):
        _push("PHONE", entry.get("phone") or "_(vazio)_", phone or "_(vazio)_")
        entry["phone"] = phone

    # Trim histórico
    if len(historico) > MAX_HISTORY:
        del historico[:-MAX_HISTORY]
    return mudancas


# ── Formatação completa do perfil para envio ──
def formatar_perfil(uid, dados: dict, viewer_id: int, db: dict) -> str:
    from access import is_owner, has_module, is_field_hidden, is_premium_user
    nome = dados.get("nome_atual", "Sem nome")
    username = dados.get("username_atual", "Nenhum")
    restricoes = dados.get("restricoes", "Nenhuma")
    fonte    = dados.get("fonte", "Varredura")
    historico = dados.get("historico", [])
    uid_str  = str(uid)
    owner    = is_owner(viewer_id)
    viewer_str = str(viewer_id)

    if is_field_hidden(dados, "id") and not owner:
        id_text = "🔒 _Oculto_"
    else:
        id_text = f"`{uid}`"
        if owner and is_field_hidden(dados, "id"):
            id_text += " _(oculto para outros)_"

    if is_field_hidden(dados, "username") and not owner:
        username_text = "🔒 _Oculto_"
    else:
        username_text = f"`{username}`"
        if owner and is_field_hidden(dados, "username"):
            username_text += " _(oculto para outros)_"

    bio_raw = dados.get("bio", "")
    if is_field_hidden(dados, "bio") and not owner:
        bio_text = "🔒 _Oculto_"
    elif has_module(db, viewer_str, "bio") or owner:
        bio_text = f"`{bio_raw[:120]}`" if bio_raw else "_Nenhuma_"
        if owner and is_field_hidden(dados, "bio"):
            bio_text += " _(oculto para outros)_"
    else:
        bio_text = f"`{bio_raw[:120]}`" if bio_raw else "_Nenhuma_"

    phone_text = exibir_telefone(dados, viewer_id, db)

    grupos = dados.get("grupos", [])
    if owner or has_module(db, viewer_str, "groups_full"):
        g_show, g_extra = grupos, ""
    else:
        max_g = max(1, len(grupos) // 5) if grupos else 0
        g_show = grupos[:max_g]
        g_extra = f" _(+{len(grupos)-max_g} ocultos — Premium)_" if len(grupos) > max_g else ""
    grupos_text = ", ".join(g_show[:8]) or "N/A"
    if len(g_show) > 8:
        grupos_text += f" (+{len(g_show)-8})"
    grupos_text += g_extra

    total_ch = len(historico)
    recent   = historico[-5:]
    hist_emoji = {"NOME": "📛", "USER": "🆔", "BIO": "📝", "PHONE": "📱"}
    hist_text = ""
    for h in reversed(recent):
        emoji = hist_emoji.get(h.get("tipo"), "🔄")
        hist_text += f"  {emoji} `{h['data']}` — {h['de']} ➜ {h['para']}\n"
    if not hist_text:
        hist_text = "  _Nenhuma alteração registrada_\n"

    first_seen  = historico[0]["data"]  if historico else "N/A"
    last_change = historico[-1]["data"] if historico else "N/A"

    is_prem  = is_premium_user(db, uid_str)
    prem_tag = " ⭐ *PREMIUM*" if (is_prem and owner) else ""

    user_clean = (username or "").lstrip("@")
    if user_clean and user_clean.lower() != "nenhum":
        link_md = f"[abrir](tg://user?id={uid}) • [t.me/{user_clean}](https://t.me/{user_clean})"
    else:
        link_md = f"[abrir](tg://user?id={uid})"

    return (
        f"╔══════════════════════════╗\n"
        f"║  🕵️ *PERFIL DO USUÁRIO*  ║\n"
        f"╚══════════════════════════╝{prem_tag}\n\n"
        f"👤 *Nome:* `{nome}`\n"
        f"🆔 *Username:* {username_text}\n"
        f"🔢 *ID:* {id_text}\n"
        f"🔗 *Acesso:* {link_md}\n"
        f"📱 *Telefone:* {phone_text}\n"
        f"📝 *Bio:* {bio_text}\n"
        f"🚫 *Restrições:* `{restricoes}`\n"
        f"📡 *Fonte:* `{fonte}`\n"
        f"📂 *Grupos:* _{grupos_text}_\n\n"
        f"📊 *Resumo:*\n"
        f"├ 📝 Total de alterações: *{total_ch}*\n"
        f"├ 📅 Primeiro registro: `{first_seen}`\n"
        f"└ 🕐 Última alteração: `{last_change}`\n\n"
        f"📜 *Últimas Alterações:*\n"
        f"{hist_text}\n"
        f"_Créditos: @Edkd1_"
    )
