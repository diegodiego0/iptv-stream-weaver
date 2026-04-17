# ══════════════════════════════════════════════
# 🎮  HANDLERS — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Handlers do bot (comandos, callbacks, texto livre, inline).
Registra todos os eventos no client `bot` recebido.
"""

import asyncio
import os
import tempfile
from datetime import datetime

from telethon import events, Button

from config import (
    OWNER_ID, BOT_USERNAME, BOT_INLINE_PATTERN,
    ITEMS_PER_PAGE, PREMIUM_MODULES,
    DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM_TOTAL,
    DAILY_LIMIT_PREMIUM_OWN, DAILY_LIMIT_PREMIUM_EXTRA,
)
from db import carregar_dados, salvar_dados, log, agora_str
from access import (is_owner, is_premium_user, has_module,
                    get_combo_limits)
from lang import (t, set_user_lang, get_user_lang, get_lang_default,
                   nome_idioma, idiomas_disponiveis, carregar_idiomas)
from ui import (menu_principal_buttons, voltar_button, paginar_buttons,
                lang_menu_buttons, module_selection_buttons,
                perfil_link_buttons)
from profile import formatar_perfil
from search import buscar_usuario, buscar_com_lookup, upsert_usuario_externo
from combo import gerar_combo_para_usuario
from quota import get_used, remaining, add_used
import scan as scan_mod
from dm import salvar_usuario_dm
from format import to_html


# ── Estado por chat ──
pending_states     = {}   # {chat_id: {"action": str, "data": {}}}
pending_module_sel = {}   # {chat_id: {"target": uid, "modules": set()}}
search_cache       = {}   # {chat_id: {"query","results_ids","username_only"}}


# ──────────────────────────────────────────────
# Suporte a "perfil completo" do usuário a partir do banco
async def _send_perfil(bot, chat_id, uid, viewer_id):
    db = carregar_dados()
    if uid not in db:
        await bot.send_message(chat_id, to_html("❌ Usuário não encontrado no banco."),
                               parse_mode='html', buttons=voltar_button(viewer_id))
        return
    text = formatar_perfil(uid, db[uid], viewer_id, db)
    await bot.send_message(
        chat_id, to_html(text), parse_mode='html',
        buttons=[
            *perfil_link_buttons(db[uid]),
            [Button.inline("📜 Histórico", f"hist_{uid}_page_0".encode())],
            *voltar_button(viewer_id),
        ],
        link_preview=False,
    )


async def _enviar_resultados(bot, event, query, results, viewer_id, db,
                              page=0, edit=False):
    chat_id = event.chat_id
    if not results:
        text = t("search_no_results", viewer_id, q=query)
        if edit:
            await event.edit(to_html(text), parse_mode='html', buttons=voltar_button(viewer_id))
        else:
            await bot.send_message(chat_id, to_html(text), parse_mode='html',
                                    buttons=voltar_button(viewer_id))
        return

    total       = len(results)
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page        = max(0, min(page, total_pages - 1))
    start       = page * ITEMS_PER_PAGE
    chunk       = results[start:start + ITEMS_PER_PAGE]

    search_cache[chat_id] = {
        "query": query,
        "results_ids": [str(r["id"]) for r in results],
    }

    text = (f"🔍 *{total} resultado(s) para* `{query}`  —  pág. "
            f"{page+1}/{total_pages}\n\n")
    btns = []
    for r in chunk:
        label = f"👤 {r.get('nome_atual','?')} | {r.get('username_atual','?')}"
        btns.append([Button.inline(label[:48], f"profile_{r['id']}".encode())])

    nav = []
    if page > 0:
        nav.append(Button.inline("◀️", f"searchpg_{page-1}".encode()))
    nav.append(Button.inline(f"📄 {page+1}/{total_pages}", b"noop"))
    if page < total_pages - 1:
        nav.append(Button.inline("▶️", f"searchpg_{page+1}".encode()))
    if len(nav) > 1:
        btns.append(nav)
    btns.append([Button.inline(t("btn_back_menu", viewer_id), b"cmd_menu")])

    if edit:
        await event.edit(to_html(text), parse_mode='html', buttons=btns, link_preview=False)
    else:
        await bot.send_message(chat_id, to_html(text), parse_mode='html',
                                buttons=btns, link_preview=False)


# ──────────────────────────────────────────────
def register_handlers(bot, user_client):

    # ─── /start ───
    @bot.on(events.NewMessage(pattern=r'^/start(?:\s|$)'))
    async def cmd_start(event):
        if event.is_private:
            sender = await event.get_sender()
            asyncio.create_task(salvar_usuario_dm(bot, sender))
        owner = is_owner(event.sender_id)
        uid   = event.sender_id
        role  = t("role_owner", uid) if owner else t("role_user", uid)
        await event.respond(
            to_html(t("start_card", uid, bot=BOT_USERNAME, role=role)),
            parse_mode='html',
            buttons=menu_principal_buttons(owner, uid),
            link_preview=False,
        )

    @bot.on(events.NewMessage(pattern=r'^/menu(?:\s|$)'))
    async def cmd_menu_msg(event):
        await cmd_start(event)

    @bot.on(events.NewMessage(pattern=r'^/lang(?:\s|$)'))
    async def cmd_lang_msg(event):
        uid = event.sender_id
        await event.respond(to_html(t("lang_menu", uid)), parse_mode='html',
                            buttons=lang_menu_buttons(uid))

    # ─── /buscar <termo> (única forma de busca direta) ───
    @bot.on(events.NewMessage(pattern=r'^/buscar(?:\s+(.+))?$'))
    async def cmd_buscar_text(event):
        if event.is_private:
            sender = await event.get_sender()
            asyncio.create_task(salvar_usuario_dm(bot, sender))
        m = event.pattern_match.group(1)
        if not m:
            await event.respond(
                to_html(t("search_prompt", event.sender_id, bot=BOT_USERNAME)),
                parse_mode='html', buttons=voltar_button(event.sender_id),
            )
            return
        query   = m.strip()
        results = await buscar_com_lookup(user_client, query, fonte="Busca direta")
        db      = carregar_dados()
        await _enviar_resultados(bot, event, query, results, event.sender_id, db)

    # ─── /setcombo (owner) ───
    @bot.on(events.NewMessage(pattern=r'^/setcombo\s+(.+)$'))
    async def cmd_setcombo(event):
        if not is_owner(event.sender_id):
            await event.respond(t("owner_only", event.sender_id)); return
        parts = event.pattern_match.group(1).split()
        if len(parts) != 3:
            await event.respond(
                to_html("Uso: `/setcombo <uid|@user|global> <free> <premium>`"),
                parse_mode='html'); return
        target, free_s, prem_s = parts
        try:
            free_v, prem_v = int(free_s), int(prem_s)
        except ValueError:
            await event.respond("❌ Limites devem ser inteiros."); return
        db = carregar_dados()
        if target == "global":
            db.setdefault("_settings", {})["free_combo_limit"]    = free_v
            db["_settings"]["premium_combo_limit"]                = prem_v
            salvar_dados(db)
            await event.respond(
                to_html(f"✅ Globais → free: *{free_v}* / premium: *{prem_v}*"),
                parse_mode='html'); return
        # Resolve target → uid
        if target.isdigit():
            uid = target
        else:
            r_uid, _, _, _ = await upsert_usuario_externo(
                user_client, target, fonte="setcombo")
            if not r_uid:
                await event.respond("❌ Alvo não encontrado."); return
            uid = r_uid
            db = carregar_dados()
        db.setdefault(uid, {}).setdefault("custom_combo_limits", {})
        db[uid]["custom_combo_limits"]["free"]    = free_v
        db[uid]["custom_combo_limits"]["premium"] = prem_v
        salvar_dados(db)
        await event.respond(
            to_html(f"✅ `{uid}` → free: *{free_v}* / premium: *{prem_v}*"),
            parse_mode='html')

    # ─── INLINE: SOMENTE @username ───
    @bot.on(events.InlineQuery)
    async def inline_query(event):
        q = (event.text or "").strip().lstrip('@')
        if not q:
            await event.answer([], switch_pm="Buscar via DM",
                                switch_pm_param="start"); return
        # Aceita apenas username (alfanumérico/_, 4–32 chars, começa por letra)
        import re
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]{3,31}$', q):
            await event.answer([], switch_pm="Use apenas @username",
                                switch_pm_param="start"); return
        results = await buscar_com_lookup(user_client, q,
                                           fonte="Inline", username_only=True)
        db = carregar_dados()
        articles = []
        for r in results[:10]:
            uid = str(r["id"])
            text = formatar_perfil(uid, db.get(uid, r), event.sender_id, db)
            articles.append(event.builder.article(
                title=f"{r.get('nome_atual','?')}",
                description=r.get('username_atual','Nenhum'),
                text=to_html(text), parse_mode='html',
            ))
        await event.answer(articles or [],
                            switch_pm="Não encontrado — abrir bot",
                            switch_pm_param="start")

    # ─── TEXTO LIVRE EM DM ───
    @bot.on(events.NewMessage(func=lambda e: e.is_private and
                              not (e.text or '').startswith('/')))
    async def text_handler(event):
        chat_id   = event.chat_id
        sender_id = event.sender_id
        text      = (event.text or "").strip()

        sender = await event.get_sender()
        asyncio.create_task(salvar_usuario_dm(bot, sender))

        # Estados pendentes (busca interativa, ocultar, premium add/remove)
        st = pending_states.get(chat_id)
        if st:
            action = st["action"]
            pending_states.pop(chat_id, None)

            if action == "search":
                results = await buscar_com_lookup(user_client, text,
                                                    fonte="Busca interativa")
                db = carregar_dados()
                await _enviar_resultados(bot, event, text, results,
                                          sender_id, db)
                return

            if action == "premium_add":
                uid_resolved, _, _, _ = await upsert_usuario_externo(
                    user_client, text, fonte="Premium add")
                if not uid_resolved:
                    await event.respond(to_html(t("user_not_found", sender_id, q=text)),
                                        parse_mode='html',
                                        buttons=voltar_button(sender_id)); return
                pending_module_sel[chat_id] = {"target": uid_resolved,
                                                "modules": set()}
                await event.respond(
                    to_html(f"⭐ Selecionar módulos para `{uid_resolved}`"),
                    parse_mode='html',
                    buttons=module_selection_buttons(set(), uid_resolved),
                ); return

            if action == "premium_remove":
                db = carregar_dados()
                target = text.strip().lstrip('@')
                uid_t = None
                if target.isdigit() and target in db:
                    uid_t = target
                else:
                    for k, v in db.items():
                        if k.startswith("_"): continue
                        if (v.get("username_atual","").lstrip('@').lower()
                            == target.lower()):
                            uid_t = k; break
                if not uid_t:
                    await event.respond("❌ Não encontrado.",
                                        buttons=voltar_button(sender_id)); return
                db[uid_t].setdefault("premium", {})["active"] = False
                db[uid_t]["premium"]["modules"] = []
                salvar_dados(db)
                await event.respond(to_html(f"✅ Premium removido de `{uid_t}`"),
                                    parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            if action and action.startswith("ocultar:"):
                field = action.split(":", 1)[1]
                db = carregar_dados()
                target = text.strip().lstrip('@')
                uid_t = None
                if target.isdigit():
                    uid_t = target
                else:
                    for k, v in db.items():
                        if k.startswith("_"): continue
                        if (v.get("username_atual","").lstrip('@').lower()
                            == target.lower()):
                            uid_t = k; break
                if not uid_t or uid_t not in db:
                    r_uid, _, _, _ = await upsert_usuario_externo(
                        user_client, target, fonte="Ocultar")
                    if not r_uid:
                        await event.respond("❌ Alvo não encontrado.",
                                            buttons=voltar_button(sender_id))
                        return
                    uid_t = r_uid
                    db = carregar_dados()
                hidden = db[uid_t].setdefault("hidden_info", {})
                hidden[field] = not hidden.get(field, False)
                salvar_dados(db)
                state = "🙈 oculto" if hidden[field] else "👁 visível"
                await event.respond(
                    to_html(f"✅ Campo `{field}` agora está {state} para `{uid_t}`"),
                    parse_mode='html', buttons=voltar_button(sender_id))
                return

        # Sem estado pendente: dica
        await event.respond(
            to_html(t("hint_use_start", sender_id, bot=BOT_USERNAME)),
            parse_mode='html', buttons=voltar_button(sender_id))

    # ──────────────────────────────────────────
    @bot.on(events.CallbackQuery)
    async def callback_handler(event):
        data      = event.data.decode()
        chat_id   = event.chat_id
        sender_id = event.sender_id
        owner     = is_owner(sender_id)

        try:
            message = await event.get_message()

            # ── Menu / navegação ──
            if data == "cmd_menu":
                await message.edit(
                    to_html(t("menu_title", sender_id)), parse_mode='html',
                    buttons=menu_principal_buttons(owner, sender_id))
                return

            if data == "cmd_lang":
                await message.edit(to_html(t("lang_menu", sender_id)), parse_mode='html',
                                    buttons=lang_menu_buttons(sender_id)); return

            if data.startswith("setlang|"):
                parts = data.split("|")
                if len(parts) == 3 and parts[1] == "default":
                    if not owner:
                        await event.answer(t("owner_only", sender_id),
                                            alert=True); return
                    code = parts[2]
                    if code not in idiomas_disponiveis():
                        await event.answer("?", alert=True); return
                    db = carregar_dados()
                    db.setdefault("_settings", {})["lang_default"] = code
                    salvar_dados(db)
                    await event.answer(f"📌 default → {nome_idioma(code)}")
                else:
                    code = parts[1]
                    if code not in idiomas_disponiveis():
                        await event.answer("?", alert=True); return
                    set_user_lang(sender_id, code)
                    await event.answer(t("lang_changed", sender_id,
                                         name=nome_idioma(code)))
                await message.edit(to_html(t("lang_menu", sender_id)), parse_mode='html',
                                    buttons=lang_menu_buttons(sender_id)); return

            if data == "cmd_buscar":
                pending_states[chat_id] = {"action": "search", "data": {}}
                await message.edit(
                    to_html(t("search_prompt", sender_id, bot=BOT_USERNAME)),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "cmd_about":
                await message.edit(to_html(t("about_text", sender_id)), parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            if data == "cmd_config":
                await message.edit(to_html(t("config_text", sender_id)), parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            if data == "cmd_stats":
                db = carregar_dados()
                total = sum(1 for k in db if not k.startswith("_"))
                prem  = sum(1 for k, v in db.items()
                            if not k.startswith("_") and
                            v.get("premium", {}).get("active"))
                chg   = sum(len(v.get("historico", []))
                            for k, v in db.items() if not k.startswith("_"))
                last  = scan_mod.scan_stats.get("last_scan") or "—"
                await message.edit(
                    to_html(t("stats_title", sender_id, total=total, prem=prem,
                      chg=chg, last=last)),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "cmd_recent":
                db = carregar_dados()
                allh = []
                for k, v in db.items():
                    if k.startswith("_"): continue
                    for h in v.get("historico", [])[-3:]:
                        allh.append((h.get("data", ""), k, v.get("nome_atual","?"), h))
                allh.sort(key=lambda x: x[0], reverse=True)
                if not allh:
                    txt = t("recent_title", sender_id) + t("recent_empty", sender_id)
                else:
                    txt = t("recent_title", sender_id)
                    for data_h, uid, nome, h in allh[:10]:
                        em = {"NOME":"📛","USER":"🆔","BIO":"📝","PHONE":"📱"}.get(
                            h.get("tipo"), "🔄")
                        txt += (f"{em} `{data_h}` `{nome}`\n"
                                f"  {h['de']} ➜ {h['para']}\n")
                await message.edit(to_html(txt), parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            # ── Perfil ──
            if data.startswith("profile_"):
                uid = data[len("profile_"):]
                db  = carregar_dados()
                if uid not in db:
                    await event.answer("❌ Não encontrado.", alert=True); return
                await message.edit(
                    to_html(formatar_perfil(uid, db[uid], sender_id, db)),
                    parse_mode='html',
                    buttons=[
                        *perfil_link_buttons(db[uid]),
                        [Button.inline("📜 Histórico",
                                       f"hist_{uid}_page_0".encode())],
                        *voltar_button(sender_id),
                    ],
                    link_preview=False,
                ); return

            if data.startswith("hist_"):
                rest = data[len("hist_"):]
                try:
                    if "_page_" in rest:
                        uid, page_s = rest.rsplit("_page_", 1)
                    else:
                        uid, page_s = rest.rsplit("_", 1)
                    page = int(page_s)
                except (ValueError, IndexError):
                    await event.answer("⚠️ Histórico inválido.", alert=True); return
                db = carregar_dados()
                if uid not in db:
                    await event.answer("❌ Sem dados.", alert=True); return
                viewer_str = str(sender_id)
                prem = is_premium_user(db, viewer_str) or owner
                hist = list(reversed(db[uid].get("historico", [])))
                if not prem:
                    hist = hist[:max(1, len(hist)//5)]
                total_pages = max(1, (len(hist)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE)
                page = max(0, min(page, total_pages-1))
                chunk = hist[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
                txt = (f"📜 *Histórico de* `{db[uid]['nome_atual']}`\n"
                       f"ID: `{uid}` — pág. {page+1}/{total_pages}\n\n")
                em_map = {"NOME":"📛","USER":"🆔","BIO":"📝","PHONE":"📱"}
                for h in chunk:
                    em = em_map.get(h.get("tipo"), "🔄")
                    txt += (f"{em} `{h['data']}`\n  {h['de']} ➜ {h['para']}\n"
                            f"  📍 _{h.get('grupo','N/A')}_\n\n")
                if not chunk:
                    txt += "_Sem registros._"
                if not prem:
                    txt += "⚠️ _Histórico limitado (Free)._"
                await message.edit(to_html(txt), parse_mode='html',
                                    buttons=paginar_buttons(
                                        f"hist_{uid}", page, total_pages,
                                        sender_id)); return

            # ── Paginação de busca (cache) ──
            if data.startswith("searchpg_"):
                try:
                    page = int(data.split("_", 1)[1])
                except ValueError:
                    await event.answer("⚠️", alert=True); return
                cache = search_cache.get(chat_id)
                if not cache:
                    # Sem cache — pede nova busca em vez de mostrar "expirou"
                    pending_states[chat_id] = {"action": "search", "data": {}}
                    await message.edit(
                        to_html("🔍 Digite novamente o que deseja buscar."),
                        parse_mode='html', buttons=voltar_button(sender_id)); return
                db = carregar_dados()
                results = [{**db[uid], "id": uid}
                           for uid in cache["results_ids"] if uid in db]
                await _enviar_resultados(bot, event, cache["query"], results,
                                          sender_id, db, page=page, edit=True)
                return

            # ── COMBO ──
            if data == "combo_run":
                viewer_str = str(sender_id)
                db = carregar_dados()
                is_prem = is_premium_user(db, viewer_str) or owner
                # Quota diária
                daily_total = (DAILY_LIMIT_PREMIUM_TOTAL if is_prem
                               else DAILY_LIMIT_FREE)
                used = get_used(viewer_str)
                rem  = max(0, daily_total - used)
                if rem <= 0:
                    await message.edit(
                        to_html(t("combo_quota_exceeded", sender_id,
                          used=used, total=daily_total)),
                        parse_mode='html', buttons=voltar_button(sender_id))
                    return
                await event.answer(f"📋 Gerando até {rem} combos...")
                msg_temp = await bot.send_message(
                    chat_id,
                    to_html(t("combo_generating", sender_id, lim=rem)),
                    parse_mode='html',
                    buttons=[[Button.inline("❌ Cancelar", b"cmd_menu")]])
                # Override de limites para respeitar o que sobrou hoje
                from combo import gerar_combo_para_usuario
                # Ajusta limites para não passar do `rem`
                # Dica: se rem < 800 (premium), reduz own
                combos, stats = await gerar_combo_para_usuario(
                    user_client, sender_id, is_prem)
                # Aplica limite remanescente
                combos = combos[:rem]
                if not combos:
                    if stats["groups_own"] == 0 and stats["groups_extra"] == 0:
                        await msg_temp.edit(
                            to_html(t("combo_no_groups", sender_id)),
                            parse_mode='html',
                            buttons=voltar_button(sender_id))
                    else:
                        await msg_temp.edit(
                            to_html(t("combo_none", sender_id)),
                            parse_mode='html',
                            buttons=voltar_button(sender_id))
                    return
                # Persiste contagem
                add_used(viewer_str, len(combos))
                # Gera arquivo
                with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(f"# Combo gerado por @{BOT_USERNAME}\n")
                    f.write(f"# Usuário: {viewer_str} | Total: {len(combos)} | "
                            f"{datetime.now()}\n")
                    f.write(f"# Próprios: {stats['own']}  Extras: {stats['extra']}\n\n")
                    f.write("\n".join(combos))
                    tmp_path = f.name
                caption = (
                    f"📋 *{len(combos)} combos gerados!*\n"
                    f"├ De seus grupos: *{stats['own']}*\n"
                    f"├ De outros grupos: *{stats['extra']}*\n"
                    f"├ Usado hoje: *{get_used(viewer_str)}/{daily_total}*\n"
                    f"└ _@Edkd1_"
                )
                await bot.send_file(chat_id, tmp_path,
                                     caption=to_html(caption), parse_mode='html')
                os.unlink(tmp_path)
                await msg_temp.delete()
                return

            # ── Owner: scan / export / ocultar / premium / combo cfg ──
            if data == "cmd_scan":
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                if scan_mod.is_scan_running():
                    await event.answer(t("scan_running", sender_id),
                                        alert=True); return
                await event.answer("🔄 Varredura iniciada")
                asyncio.create_task(scan_mod.executar_varredura(
                    user_client, bot, notify_chat=chat_id))
                return

            if data == "cmd_export":
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                from config import FILE_PATH
                if os.path.exists(FILE_PATH):
                    await bot.send_file(chat_id, FILE_PATH,
                                         caption="📤 Banco completo")
                await event.answer("✅"); return

            if data == "cmd_ocultar_menu":
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                rows = [
                    [Button.inline("📵 Telefone",  b"ocultar:phone"),
                     Button.inline("🔒 ID",        b"ocultar:id")],
                    [Button.inline("👤 Username",  b"ocultar:username"),
                     Button.inline("📝 Bio",        b"ocultar:bio")],
                    *voltar_button(sender_id),
                ]
                await message.edit(
                    to_html("🙈 *Ocultar Informações*\n\nEscolha o campo:"),
                    parse_mode='html', buttons=rows); return

            if data.startswith("ocultar:"):
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                field = data.split(":",1)[1]
                pending_states[chat_id] = {"action": f"ocultar:{field}",
                                            "data": {}}
                await message.edit(
                    to_html(f"🙈 Envie o *ID* ou *@username* do alvo "
                    f"para alternar o campo `{field}`:"),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "cmd_premium_menu":
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                rows = [
                    [Button.inline("➕ Adicionar Premium", b"prem_add")],
                    [Button.inline("➖ Remover Premium",   b"prem_rem")],
                    [Button.inline("📋 Listar Premiums",   b"prem_list")],
                    *voltar_button(sender_id),
                ]
                await message.edit(
                    to_html("⭐ *Gerenciar Premium*"), parse_mode='html', buttons=rows); return

            if data == "prem_add":
                if not owner: return
                pending_states[chat_id] = {"action":"premium_add", "data":{}}
                await message.edit(
                    to_html("➕ Envie o *ID* ou *@username* do alvo:"),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "prem_rem":
                if not owner: return
                pending_states[chat_id] = {"action":"premium_remove", "data":{}}
                await message.edit(
                    to_html("➖ Envie o *ID* ou *@username* para remover premium:"),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "prem_list":
                if not owner: return
                db = carregar_dados()
                lst = [(k,v) for k,v in db.items() if not k.startswith("_")
                       and v.get("premium",{}).get("active")]
                if not lst:
                    txt = "_Nenhum usuário premium cadastrado._"
                else:
                    txt = "⭐ *Usuários Premium:*\n\n"
                    for k,v in lst[:30]:
                        mods = ", ".join(v["premium"].get("modules",[])) or "—"
                        txt += f"• `{k}` `{v.get('nome_atual','?')}` _({mods})_\n"
                await message.edit(to_html(txt), parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            if data.startswith("tmod|"):
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                _, target_uid, mod_key = data.split("|", 2)
                sel = pending_module_sel.setdefault(
                    chat_id, {"target": target_uid, "modules": set()}
                )["modules"]
                if mod_key in sel:
                    sel.remove(mod_key)
                else:
                    sel.add(mod_key)
                await message.edit(
                    to_html(f"⭐ Selecionar módulos para `{target_uid}`"),
                    parse_mode='html',
                    buttons=module_selection_buttons(sel, target_uid)); return

            if data.startswith("cprem|"):
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                target_uid = data.split("|",1)[1]
                sel = pending_module_sel.get(chat_id, {}).get("modules", set())
                db = carregar_dados()
                if target_uid not in db:
                    await event.answer("❌ Alvo sumiu do banco.", alert=True); return
                db[target_uid].setdefault("premium", {})
                db[target_uid]["premium"]["active"]  = True
                db[target_uid]["premium"]["modules"] = list(sel)
                salvar_dados(db)
                pending_module_sel.pop(chat_id, None)
                mods_txt = "\n".join(
                    f"• {PREMIUM_MODULES[m]}" for m in sel) or "_(nenhum)_"
                await message.edit(
                    to_html(f"✅ *Premium ativado!*\n\n👤 `{db[target_uid].get('nome_atual','?')}` "
                    f"(`{target_uid}`)\n\n*Módulos:*\n{mods_txt}"),
                    parse_mode='html', buttons=voltar_button(sender_id)); return

            if data == "cmd_combo_config":
                if not owner:
                    await event.answer(t("owner_only", sender_id),
                                        alert=True); return
                db = carregar_dados()
                f_lim = db.get("_settings",{}).get("free_combo_limit",
                                                    DAILY_LIMIT_FREE)
                p_lim = db.get("_settings",{}).get("premium_combo_limit",
                                                    DAILY_LIMIT_PREMIUM_TOTAL)
                txt = (
                    "🎛️ *Configuração de Combo*\n\n"
                    f"📊 *Limites globais:*\n"
                    f"├ Free: *{f_lim}* linhas/dia\n"
                    f"└ Premium: *{p_lim}* linhas/dia\n\n"
                    "Para alterar:\n"
                    "`/setcombo global <free> <premium>`\n"
                    "`/setcombo <uid|@user> <free> <premium>`"
                )
                await message.edit(to_html(txt), parse_mode='html',
                                    buttons=voltar_button(sender_id)); return

            if data == "noop":
                await event.answer(); return

            log(f"⚠️ Callback não roteado: {data!r}")
            await event.answer("⚠️ Ação não reconhecida.", alert=True)

        except Exception as e:
            log(f"❌ Callback [{data}]: {type(e).__name__}: {e}")
            try:
                await event.answer("❌ Erro interno. Veja os logs.", alert=True)
            except Exception:
                pass
