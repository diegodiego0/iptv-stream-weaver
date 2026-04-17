# ══════════════════════════════════════════════
# 🎨  BOTÕES & MENUS — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════

from telethon import Button
from access import is_owner
from lang import t, get_user_lang, get_lang_default, idiomas_disponiveis, nome_idioma
from config import PREMIUM_MODULES


def menu_principal_buttons(owner: bool = False, uid=None) -> list:
    base = [
        [Button.inline(t("btn_buscar", uid),  b"cmd_buscar"),
         Button.inline(t("btn_stats",  uid),  b"cmd_stats")],
        [Button.inline("📋 Gerar Combo",      b"combo_run"),
         Button.inline(t("btn_recent", uid),  b"cmd_recent")],
        [Button.inline(t("btn_config", uid),  b"cmd_config"),
         Button.inline(t("btn_about",  uid),  b"cmd_about")],
        [Button.inline(t("btn_lang",   uid),  b"cmd_lang")],
    ]
    if owner:
        base.insert(1, [
            Button.inline(t("btn_scan",   uid), b"cmd_scan"),
            Button.inline(t("btn_export", uid), b"cmd_export"),
        ])
        base.insert(2, [
            Button.inline(t("btn_ocultar", uid), b"cmd_ocultar_menu"),
            Button.inline(t("btn_premium", uid), b"cmd_premium_menu"),
        ])
        base.insert(3, [
            Button.inline(t("btn_combo_cfg", uid), b"cmd_combo_config"),
        ])
    return base


def voltar_button(uid=None) -> list:
    return [[Button.inline(t("btn_back_menu", uid), b"cmd_menu")]]


def paginar_buttons(prefix: str, page: int, total_pages: int, uid=None) -> list:
    nav = []
    if page > 0:
        nav.append(Button.inline("◀️", f"{prefix}_page_{page-1}".encode()))
    nav.append(Button.inline(f"📄 {page+1}/{total_pages}", b"noop"))
    if page < total_pages - 1:
        nav.append(Button.inline("▶️", f"{prefix}_page_{page+1}".encode()))
    return [nav, [Button.inline(t("btn_back_menu", uid), b"cmd_menu")]]


def lang_menu_buttons(uid=None) -> list:
    rows = []
    current = get_user_lang(uid) if uid is not None else get_lang_default()
    for code in idiomas_disponiveis():
        mark = "✅ " if code == current else ""
        rows.append([Button.inline(f"{mark}{nome_idioma(code)}",
                                   f"setlang|{code}".encode())])
    if uid is not None and is_owner(uid):
        rows.append([Button.inline("📌 Salvar como padrão (owner)",
                                   f"setlang|default|{current}".encode())])
    rows.append([Button.inline(t("btn_back_menu", uid), b"cmd_menu")])
    return rows


def module_selection_buttons(selected: set, target_uid: str) -> list:
    rows = []
    for mod_key, mod_label in PREMIUM_MODULES.items():
        mark  = "✅" if mod_key in selected else "⬜"
        rows.append([Button.inline(f"{mark} {mod_label}",
                                   f"tmod|{target_uid}|{mod_key}".encode())])
    rows.append([
        Button.inline("✔️ Confirmar",  f"cprem|{target_uid}".encode()),
        Button.inline("❌ Cancelar",   b"cmd_premium_menu"),
    ])
    return rows


def perfil_link_buttons(dados: dict) -> list:
    rows = []
    user = (dados.get("username_atual") or "").lstrip("@")
    if user and user.lower() != "nenhum":
        rows.append([Button.url("🔗 Abrir no Telegram", f"https://t.me/{user}")])
    return rows
