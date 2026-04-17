# ══════════════════════════════════════════════
# 🌐  i18n — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Sistema de idiomas dinâmico. lang.json fica na MESMA pasta do bot.
Se não existir, é criado com PT-BR / EN / ES por padrão.
"""

import json
import os
import time
from config import LANG_FILE, FILE_PATH, DEFAULT_HIDDEN
from db import carregar_dados, salvar_dados


DEFAULT_LANG_DATA = {
    "_meta": {
        "version": "1.0",
        "default": "pt_br",
        "available": ["pt_br", "en", "es"],
        "names": {
            "pt_br": "🇧🇷 Português (BR)",
            "en":    "🇺🇸 English",
            "es":    "🇪🇸 Español",
        },
    },
    "pt_br": {
        "menu_title":  "🕵️ *User Info Bot Pro v7.0*\n\nSelecione uma opção:",
        "start_card":  ("╔══════════════════════════════╗\n"
                        "║  🕵️ *User Info Bot Pro v7.0*  ║\n"
                        "╚══════════════════════════════╝\n\n"
                        "Monitor profissional de usuários Telegram.\n\n"
                        "🔍 Busca direta apenas via DM com `/buscar <termo>`\n"
                        "💡 Inline: `@{bot} @username` (apenas username)\n\n"
                        "{role}\n\n👨‍💻 _Créditos: Edivaldo Silva @Edkd1_"),
        "role_owner":  "⭐ Painel owner ativo",
        "role_user":   "👤 Modo usuário",
        "btn_buscar":  "🔍 Buscar Usuário",
        "btn_stats":   "📊 Estatísticas",
        "btn_recent":  "📋 Últimas Alterações",
        "btn_config":  "⚙️ Configurações",
        "btn_about":   "ℹ️ Sobre",
        "btn_lang":    "🌐 Idioma",
        "btn_scan":    "🔄 Varredura",
        "btn_export":  "📤 Exportar Banco",
        "btn_ocultar": "🙈 Ocultar info",
        "btn_premium": "⭐ Gerenciar Premium",
        "btn_combo_cfg":"🎛️ Config. Combo",
        "btn_back_menu":"🔙 Menu Principal",
        "btn_back":    "🔙 Voltar",
        "btn_history": "📜 Histórico",
        "btn_open_tg": "🔗 Abrir no Telegram",
        "btn_cancel":  "❌ Cancelar",
        "btn_confirm": "✔️ Confirmar",
        "search_prompt":("🔍 *Modo Busca*\n\nEnvie:\n"
                         "• `123456789` → por ID\n"
                         "• `@username` → por username\n"
                         "• `Nome` → por nome parcial\n\n_Aguardando..._"),
        "search_no_results":"❌ Nenhum resultado para `{q}`.",
        "owner_only":  "🚫 Restrito ao owner.",
        "user_not_found":"❌ Usuário `{q}` não encontrado.",
        "scan_running":"⚠️ Varredura já em andamento!",
        "scan_started":"🔄 *Varredura iniciada...*\n⏳ Aguarde notificação ao finalizar.",
        "scan_done":   ("✅ *Varredura Concluída!*\n\n"
                        "📂 Grupos: *{g}*\n👥 Usuários: *{u}*\n"
                        "🔔 Alterações: *{c}*\n🕐 `{ts}`"),
        "combo_generating":"⏳ *Gerando combo...*\nLimite hoje: *{lim}* linhas",
        "combo_none":  ("❌ *Nenhum combo encontrado nos seus grupos.*\n\n"
                        "Você precisa estar em pelo menos 1 grupo onde "
                        "credenciais Xtream Codes circulem."),
        "combo_done":  "📋 *{n} combos gerados!*\n_@Edkd1_",
        "combo_quota_exceeded":("🚫 *Limite diário atingido*\n\n"
                                "Você já usou *{used}/{total}* linhas hoje.\n"
                                "Tente novamente amanhã."),
        "combo_no_groups":("⚠️ *Você não está em nenhum grupo monitorado.*\n\n"
                           "Entre em grupos onde credenciais Xtream circulem "
                           "e tente novamente."),
        "lang_menu":   "🌐 *Idioma / Language / Idioma*\n\nEscolha o idioma do bot:",
        "lang_changed":"✅ Idioma alterado para *{name}*.",
        "stats_title": ("📊 *Estatísticas*\n\n"
                        "👥 Usuários: *{total}*\n"
                        "⭐ Premium: *{prem}*\n"
                        "🔄 Alterações totais: *{chg}*\n"
                        "🕐 Última varredura: `{last}`"),
        "about_text":  ("ℹ️ *User Info Bot Pro v7.0*\n\n"
                        "Monitor profissional Telegram modular.\n"
                        "Busca por ID/username/nome, histórico completo,\n"
                        "premium granular, geração de combo Xtream\n"
                        "a partir dos seus grupos, idiomas dinâmicos.\n\n"
                        "👨‍💻 _Créditos: Edivaldo Silva @Edkd1_"),
        "config_text": "⚙️ *Configurações*\n\nEscolha uma opção abaixo:",
        "recent_title":"📋 *Últimas alterações:*\n\n",
        "recent_empty":"_Sem alterações registradas._",
        "hint_use_start":"💡 Use /start para abrir o menu.\nBusca: `/buscar <termo>`",
    },
    "en": {
        "menu_title":  "🕵️ *User Info Bot Pro v7.0*\n\nSelect an option:",
        "start_card":  ("🕵️ *User Info Bot Pro v7.0*\n\n"
                        "Professional Telegram user monitor.\n\n"
                        "🔍 Direct search via DM with `/buscar <term>`\n"
                        "💡 Inline: `@{bot} @username` (username only)\n\n"
                        "{role}\n\n👨‍💻 _Credits: Edivaldo Silva @Edkd1_"),
        "role_owner":  "⭐ Owner panel active",
        "role_user":   "👤 User mode",
        "btn_buscar":  "🔍 Search User",
        "btn_stats":   "📊 Stats",
        "btn_recent":  "📋 Recent Changes",
        "btn_config":  "⚙️ Settings",
        "btn_about":   "ℹ️ About",
        "btn_lang":    "🌐 Language",
        "btn_scan":    "🔄 Scan",
        "btn_export":  "📤 Export DB",
        "btn_ocultar": "🙈 Hide info",
        "btn_premium": "⭐ Manage Premium",
        "btn_combo_cfg":"🎛️ Combo Settings",
        "btn_back_menu":"🔙 Main Menu",
        "btn_back":    "🔙 Back",
        "btn_history": "📜 History",
        "btn_cancel":  "❌ Cancel",
        "btn_confirm": "✔️ Confirm",
        "owner_only":  "🚫 Owner only.",
        "lang_menu":   "🌐 *Language*\n\nChoose your language:",
        "lang_changed":"✅ Language changed to *{name}*.",
    },
    "es": {
        "menu_title":  "🕵️ *User Info Bot Pro v7.0*\n\nSelecciona una opción:",
        "start_card":  ("🕵️ *User Info Bot Pro v7.0*\n\n"
                        "Monitor profesional de usuarios Telegram.\n\n"
                        "🔍 Búsqueda directa por DM con `/buscar <término>`\n"
                        "💡 Inline: `@{bot} @username` (solo username)\n\n"
                        "{role}\n\n👨‍💻 _Créditos: Edivaldo Silva @Edkd1_"),
        "role_owner":  "⭐ Panel owner activo",
        "role_user":   "👤 Modo usuario",
        "btn_buscar":  "🔍 Buscar",
        "btn_stats":   "📊 Estadísticas",
        "btn_back_menu":"🔙 Menú Principal",
        "lang_menu":   "🌐 *Idioma*\n\nElige tu idioma:",
        "lang_changed":"✅ Idioma cambiado a *{name}*.",
    },
}


_lang_cache = {"data": None, "ts": 0.0}


def _ensure_lang_file():
    if os.path.exists(LANG_FILE):
        return
    try:
        with open(LANG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_LANG_DATA, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"[lang] erro ao criar lang.json: {e}")


def carregar_idiomas(force: bool = False) -> dict:
    now = time.time()
    if not force and _lang_cache["data"] is not None and (now - _lang_cache["ts"]) < 5:
        return _lang_cache["data"]
    _ensure_lang_file()
    try:
        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[lang] erro ao ler lang.json, usando default: {e}")
        data = DEFAULT_LANG_DATA
    _lang_cache["data"] = data
    _lang_cache["ts"]   = now
    return data


def idiomas_disponiveis() -> list:
    return carregar_idiomas().get("_meta", {}).get("available", ["pt_br", "en", "es"])


def nome_idioma(code: str) -> str:
    return carregar_idiomas().get("_meta", {}).get("names", {}).get(code, code)


def get_lang_default() -> str:
    data = carregar_idiomas()
    try:
        db = json.load(open(FILE_PATH, 'r', encoding='utf-8')) if os.path.exists(FILE_PATH) else {}
    except Exception:
        db = {}
    return (db.get("_settings", {}) or {}).get(
        "lang_default", data.get("_meta", {}).get("default", "pt_br")
    )


def get_user_lang(user_id) -> str:
    uid = str(user_id)
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception:
        return get_lang_default()
    return db.get(uid, {}).get("lang") or get_lang_default()


def set_user_lang(user_id, code: str):
    uid = str(user_id)
    db  = carregar_dados()
    if uid not in db:
        db[uid] = {
            "id": int(user_id) if str(user_id).lstrip("-").isdigit() else user_id,
            "nome_atual": "Sem nome", "username_atual": "Nenhum",
            "fonte": "Idioma", "historico": [], "grupos": [], "grupos_ids": [],
            "hidden_info": dict(DEFAULT_HIDDEN),
            "premium": {"active": False, "modules": []},
            "custom_combo_limits": {},
        }
    db[uid]["lang"] = code
    salvar_dados(db)


def t(key: str, user_id=None, lang: str = None, **fmt) -> str:
    """Tradução com fallback pt_br → chave."""
    data = carregar_idiomas()
    if lang is None:
        lang = get_user_lang(user_id) if user_id is not None else get_lang_default()
    bundle   = data.get(lang) or {}
    fallback = data.get("pt_br") or {}
    txt = bundle.get(key, fallback.get(key, key))
    if fmt:
        try:
            return txt.format(**fmt)
        except Exception:
            return txt
    return txt
