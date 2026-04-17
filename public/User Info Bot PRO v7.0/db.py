# ══════════════════════════════════════════════
# 💾  BANCO DE DADOS — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Camada de persistência para o user_database.json.
Garante atomicidade básica e formato consistente dos registros.
"""

import json
import os
from datetime import datetime
from config import (
    FILE_PATH, LOG_PATH, DEFAULT_HIDDEN,
    DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM_TOTAL,
)


def _ensure_files():
    if not os.path.exists(FILE_PATH):
        default_db = {"_settings": {
            "free_combo_limit":    DAILY_LIMIT_FREE,
            "premium_combo_limit": DAILY_LIMIT_PREMIUM_TOTAL,
            "lang_default":        "pt_br",
        }}
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_db, f, indent=2, ensure_ascii=False)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] Log iniciado\n")


_ensure_files()


def carregar_dados() -> dict:
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except (json.JSONDecodeError, IOError):
        db = {}
    if "_settings" not in db:
        db["_settings"] = {
            "free_combo_limit":    DAILY_LIMIT_FREE,
            "premium_combo_limit": DAILY_LIMIT_PREMIUM_TOTAL,
            "lang_default":        "pt_br",
        }
    return db


def salvar_dados(db: dict):
    try:
        # write atômico simples: tmp + replace
        tmp = FILE_PATH + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        os.replace(tmp, FILE_PATH)
    except IOError as e:
        log(f"❌ Erro ao salvar banco: {e}")


def log(msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except IOError:
        pass


def iter_usuarios(db: dict):
    for k, v in db.items():
        if not k.startswith("_"):
            yield k, v


def agora_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def hoje_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_user_shape(entry: dict):
    """Garante todos os campos esperados em um registro de usuário."""
    entry.setdefault("hidden_info",   dict(DEFAULT_HIDDEN))
    entry.setdefault("premium",       {"active": False, "modules": []})
    entry.setdefault("custom_combo_limits", {})
    entry.setdefault("historico",     [])
    entry.setdefault("grupos",        [])
    entry.setdefault("grupos_ids",    [])  # IDs reais dos grupos (para combo)
    entry.setdefault("bio",           "")
    entry.setdefault("phone",         "")
    entry.setdefault("fotos",         False)
    entry.setdefault("restricoes",    "Nenhuma")
    entry.setdefault("nome_atual",    "Sem nome")
    entry.setdefault("username_atual","Nenhum")
    entry.setdefault("fonte",         "Manual")
