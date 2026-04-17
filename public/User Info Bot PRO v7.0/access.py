# ══════════════════════════════════════════════
# 🔑  CONTROLE DE ACESSO — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════

from config import OWNER_ID, DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM_TOTAL


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_premium_user(db: dict, uid: str) -> bool:
    if uid not in db or uid.startswith("_"):
        return False
    return db[uid].get("premium", {}).get("active", False)


def has_module(db: dict, uid: str, module: str) -> bool:
    if not is_premium_user(db, uid):
        return False
    return module in db[uid].get("premium", {}).get("modules", [])


def is_field_hidden(dados: dict, field: str) -> bool:
    return dados.get("hidden_info", {}).get(field, False)


def get_combo_limits(db: dict, uid: str) -> tuple:
    """Retorna (limite_free, limite_premium) levando em conta override por usuário."""
    settings       = db.get("_settings", {})
    global_free    = settings.get("free_combo_limit",    DAILY_LIMIT_FREE)
    global_premium = settings.get("premium_combo_limit", DAILY_LIMIT_PREMIUM_TOTAL)
    user_limits    = db.get(uid, {}).get("custom_combo_limits", {}) if uid in db else {}
    return (
        user_limits.get("free",    global_free),
        user_limits.get("premium", global_premium),
    )
