# ══════════════════════════════════════════════
# 📊  QUOTA DIÁRIA DE COMBOS — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Persistência simples por usuário/dia. Reset automático ao mudar de dia.
Estrutura JSON:
  { "<uid>": { "date": "YYYY-MM-DD", "used": 123 } }
"""

import json
import os
from config import COMBO_QUOTA_FILE
from db import hoje_str


def _load() -> dict:
    if not os.path.exists(COMBO_QUOTA_FILE):
        return {}
    try:
        with open(COMBO_QUOTA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    try:
        tmp = COMBO_QUOTA_FILE + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, COMBO_QUOTA_FILE)
    except IOError:
        pass


def get_used(uid: str) -> int:
    data = _load()
    entry = data.get(str(uid))
    if not entry:
        return 0
    if entry.get("date") != hoje_str():
        return 0
    return int(entry.get("used", 0))


def remaining(uid: str, daily_limit: int) -> int:
    return max(0, daily_limit - get_used(uid))


def add_used(uid: str, qty: int):
    data = _load()
    key = str(uid)
    today = hoje_str()
    entry = data.get(key, {})
    if entry.get("date") != today:
        entry = {"date": today, "used": 0}
    entry["used"] = int(entry.get("used", 0)) + max(0, int(qty))
    data[key] = entry
    _save(data)


def reset(uid: str):
    data = _load()
    data.pop(str(uid), None)
    _save(data)
