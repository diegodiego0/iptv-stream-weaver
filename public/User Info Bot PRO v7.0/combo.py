# ══════════════════════════════════════════════
# 📋  COMBO XTREAM — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Geração de combos `usuario:senha` extraídos de mensagens dos GRUPOS
EM QUE O USUÁRIO ESTÁ. Sem duplicatas. Quotas diárias por usuário.

Regras:
- Free: até 300 linhas/dia, somente dos grupos do usuário.
- Premium: até 800 linhas/dia dos próprios grupos +
           200 linhas/dia adicionais de outros grupos
           = total 1000/dia. Se grupos próprios não atingem 800,
           o restante é completado com outros grupos até 1000.

Raspagem rápida: grupos processados em paralelo (asyncio.gather + semaphore).
"""

import asyncio
from telethon.errors import FloodWaitError
from config import (
    XTREAM_PATTERNS, SCRAPE_MSG_LIMIT_PER_GROUP, SCRAPE_CONCURRENCY,
    DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM_OWN,
    DAILY_LIMIT_PREMIUM_EXTRA, DAILY_LIMIT_PREMIUM_TOTAL,
)
from db import log, carregar_dados


# ──────────────────────────────────────────────
def _extract_from_text(text: str, seen: set, out: list, limit: int) -> int:
    """Extrai combos `user:pass` de um texto. Retorna quantos foram adicionados."""
    if not text or len(out) >= limit:
        return 0
    added = 0
    for idx, pat in enumerate(XTREAM_PATTERNS):
        for m in pat.findall(text):
            # Padrão 0/2: (user, pass). Padrão 1: (pass, user) — invertido.
            if idx == 1:
                pass_part, user_part = m[0], m[1]
            else:
                user_part, pass_part = m[0], m[1]
            user_part = (user_part or "").strip()
            pass_part = (pass_part or "").strip()
            if len(user_part) < 2 or len(pass_part) < 2:
                continue
            # Evita capturar endpoints como combo (ex.: player_api:senha)
            if user_part.lower() in ("get.php", "player_api.php", "panel_api.php",
                                      "xmltv.php", "c", "live", "movie", "series"):
                continue
            combo = f"{user_part}:{pass_part}"
            if combo in seen:
                continue
            seen.add(combo)
            out.append(combo)
            added += 1
            if len(out) >= limit:
                return added
    return added


# ──────────────────────────────────────────────
async def _scrape_dialog(client, dialog, seen: set, out: list, limit: int):
    """Raspa um único diálogo (grupo/canal) por mensagens recentes."""
    if len(out) >= limit:
        return
    try:
        async for msg in client.iter_messages(dialog.id,
                                              limit=SCRAPE_MSG_LIMIT_PER_GROUP):
            if len(out) >= limit:
                break
            if not msg or not (msg.text or getattr(msg, "raw_text", "")):
                continue
            _extract_from_text(msg.text or msg.raw_text, seen, out, limit)
    except FloodWaitError as e:
        await asyncio.sleep(min(e.seconds, 30))
    except Exception as e:
        log(f"⚠️ combo scrape grupo {getattr(dialog,'name','?')}: {e}")


async def _gather_dialogs(client, dialogs, seen, out, limit):
    """Executa _scrape_dialog em paralelo respeitando SCRAPE_CONCURRENCY."""
    sem = asyncio.Semaphore(SCRAPE_CONCURRENCY)

    async def _worker(d):
        async with sem:
            if len(out) >= limit:
                return
            await _scrape_dialog(client, d, seen, out, limit)

    await asyncio.gather(*[_worker(d) for d in dialogs], return_exceptions=True)


# ──────────────────────────────────────────────
async def listar_grupos_do_usuario(user_client, target_user_id: int) -> list:
    """
    Retorna lista de Dialog onde o user alvo é membro.
    Usa o banco como cache (campo grupos_ids), e como fallback verifica
    diálogos do userbot (que precisa estar nos mesmos grupos).
    """
    db = carregar_dados()
    entry = db.get(str(target_user_id), {})
    cached_ids = set(entry.get("grupos_ids", []) or [])

    dialogs_user = []
    dialogs_other = []
    try:
        async for d in user_client.iter_dialogs():
            if not (d.is_group or d.is_channel):
                continue
            if d.id in cached_ids or str(d.id) in cached_ids:
                dialogs_user.append(d)
            else:
                dialogs_other.append(d)
    except Exception as e:
        log(f"⚠️ listar_grupos_do_usuario: {e}")

    # Se cache vazio, considera todos os diálogos do userbot como "do usuário"
    # (cenário típico: dono usa o próprio userbot).
    if not dialogs_user and not cached_ids:
        dialogs_user = dialogs_other
        dialogs_other = []

    return dialogs_user, dialogs_other


# ──────────────────────────────────────────────
async def gerar_combo_para_usuario(user_client, target_user_id: int,
                                    is_premium: bool) -> tuple:
    """
    Gera combos respeitando a regra de origem (próprios grupos / outros grupos)
    e o limite total. Retorna (combos, stats).
    stats = {"own": int, "extra": int, "groups_own": int, "groups_extra": int}
    """
    dialogs_user, dialogs_other = await listar_grupos_do_usuario(
        user_client, target_user_id
    )

    seen, out = set(), []
    stats = {"own": 0, "extra": 0,
             "groups_own": len(dialogs_user),
             "groups_extra": len(dialogs_other)}

    if is_premium:
        own_limit   = DAILY_LIMIT_PREMIUM_OWN          # 800
        total_limit = DAILY_LIMIT_PREMIUM_TOTAL        # 1000
    else:
        own_limit   = DAILY_LIMIT_FREE                  # 300
        total_limit = DAILY_LIMIT_FREE                  # 300

    # 1) Raspa dos grupos do próprio usuário até own_limit
    await _gather_dialogs(user_client, dialogs_user, seen, out, own_limit)
    stats["own"] = len(out)

    # 2) Premium: completa com outros grupos até total_limit
    if is_premium and len(out) < total_limit:
        await _gather_dialogs(user_client, dialogs_other, seen, out, total_limit)
        stats["extra"] = len(out) - stats["own"]

    # Free: estritamente nos próprios grupos. Não usa outros.
    return out[:total_limit], stats
