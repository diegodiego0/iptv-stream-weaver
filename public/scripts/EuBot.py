#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════╗
║  SILVA IPTV PANEL MANAGER + AUTOMAÇÃO PRO v7.0   ║
║  Bot Telegram + Userbot Unificado                ║
║  Gerenciamento de Painel IPTV/P2P + Automação    ║
║  Consulta URL + Inline + AutoMs + Msgs Prontas   ║
║  Auto-Reply + Gestão Usuários + Broadcast        ║
║  Painel vendedorp2p.com completo                 ║
║  👤 Dono: Edivaldo Silva                         ║
║  🆔 ID: 2061557102                               ║
║  📎 @Edkd1                                       ║
╚══════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import math
import time
import random
import socket
import asyncio
import hashlib
import requests
from io import StringIO
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin
from datetime import datetime
from requests.sessions import Session

from telethon import TelegramClient, events, Button
from telethon.tl.types import InputBotInlineResult, InputBotInlineMessageText
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# ══════════════════════════════════════════════
# CONFIGURAÇÕES GERAIS
# ══════════════════════════════════════════════

API_ID = 29214781
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102
OWNER_NAME = "Edivaldo Silva"
OWNER_CONTACT = "@Edkd1"
OWNER_USERNAME = "@Edkd1"
BOT_VERSION = "7.0 PRO"

CANAL_RESULTADOS_ID = -1003774905088
BASE_DIR = "/sdcard/EuBot"
GRUPOS_FILE = os.path.join(BASE_DIR, "grupos_permitidos.txt")
AUTOMS_FILE = os.path.join(BASE_DIR, "automs.json")
USERS_FILE = os.path.join(BASE_DIR, "usuarios.json")
AUTOREPLY_FILE = os.path.join(BASE_DIR, "autoreply.json")
MSGS_PRONTAS_FILE = os.path.join(BASE_DIR, "msgs_prontas.json")
ITEMS_PER_PAGE = 5

# ── Painel IPTV ──
PAINEL_URL = "https://vendedorp2p.com"
PAGE_SIZE = 10
SESSION_TIMEOUT = 3600
CACHE_TTL = 60

# ── Emojis ──
E = {
    "ok": "✅", "err": "❌", "warn": "⚠️", "load": "⏳",
    "user": "👤", "pass": "🔑", "credit": "💰",
    "tv": "📺", "p2p": "🔗", "rev": "👥", "online": "🟢",
    "offline": "🔴", "search": "🔎", "fast": "⚡", "create": "➕",
    "test": "🧪", "log": "📜", "tool": "⚙️", "exit": "🚪",
    "dash": "📊", "back": "🔙", "left": "⬅️", "right": "➡️",
    "conn": "🌐", "cancel": "❎", "edit": "✏️", "del": "🗑️",
    "lock": "🔐", "info": "ℹ️", "time": "🕐",
    "device": "📱", "ip": "🌍", "refresh": "🔄",
    "star": "⭐", "link": "🔗", "dns": "🌐", "port": "🚪",
    "crown": "👑", "bolt": "⚡", "fire": "🔥", "rocket": "🚀",
    "check": "☑️", "copy": "📋", "key": "🗝️",
}

LINE = "━" * 32
THIN = "─" * 30

# ══════════════════════════════════════════════
# CLIENTES TELETHON
# ══════════════════════════════════════════════

userbot = TelegramClient("userbot_silva_session", API_ID, API_HASH)
bot = TelegramClient("bot_silva_session", API_ID, API_HASH)

# ══════════════════════════════════════════════
# UTILITÁRIOS DE ARQUIVO
# ══════════════════════════════════════════════

def ensure_base_dir():
    os.makedirs(BASE_DIR, exist_ok=True)

def safe_json_load(filepath, default=None):
    ensure_base_dir()
    if default is None:
        default = []
    if not os.path.exists(filepath):
        safe_json_save(filepath, default)
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def safe_json_save(filepath, data):
    ensure_base_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════
# GESTÃO DE USUÁRIOS (registro automático)
# ══════════════════════════════════════════════

def load_users():
    return safe_json_load(USERS_FILE, [])

def save_users(users):
    safe_json_save(USERS_FILE, users)

def register_user(user_id, first_name="", last_name="", username=None):
    """Registra ou atualiza um usuário automaticamente."""
    users = load_users()
    existing = next((u for u in users if u["id"] == user_id), None)
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    if existing:
        existing["nome"] = f"{first_name} {last_name}".strip()
        existing["username"] = username
        existing["ultimo_acesso"] = now
        existing["interacoes"] = existing.get("interacoes", 0) + 1
    else:
        users.append({
            "id": user_id,
            "nome": f"{first_name} {last_name}".strip(),
            "username": username,
            "registrado_em": now,
            "ultimo_acesso": now,
            "interacoes": 1
        })
    save_users(users)

def get_user_info(user_id):
    users = load_users()
    return next((u for u in users if u["id"] == user_id), None)

def find_user(query):
    """Encontra usuário por ID, username ou nome."""
    users = load_users()
    query_str = str(query).strip().lstrip("@")
    for u in users:
        if str(u["id"]) == query_str:
            return u
        if u.get("username") and u["username"].lower() == query_str.lower():
            return u
    return None

# ══════════════════════════════════════════════
# GESTÃO DE GRUPOS PERMITIDOS
# ══════════════════════════════════════════════

def load_groups():
    ensure_base_dir()
    if not os.path.exists(GRUPOS_FILE):
        with open(GRUPOS_FILE, "w") as f:
            f.write("")
        return []
    with open(GRUPOS_FILE, "r") as f:
        lines = f.read().strip().split("\n")
    groups = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parts = line.split("|", 1)
            gid = int(parts[0].strip())
            name = parts[1].strip() if len(parts) > 1 else "Sem nome"
            groups.append({"id": gid, "name": name})
        except ValueError:
            continue
    return groups

def save_groups(groups):
    ensure_base_dir()
    with open(GRUPOS_FILE, "w") as f:
        for g in groups:
            f.write(f"{g['id']}|{g['name']}\n")

def is_group_allowed(chat_id):
    groups = load_groups()
    return any(g["id"] == chat_id for g in groups)

def add_group(chat_id, name):
    groups = load_groups()
    if any(g["id"] == chat_id for g in groups):
        return False
    groups.append({"id": chat_id, "name": name})
    save_groups(groups)
    return True

def remove_group(chat_id):
    groups = load_groups()
    new_groups = [g for g in groups if g["id"] != chat_id]
    if len(new_groups) == len(groups):
        return False
    save_groups(new_groups)
    return True

# ══════════════════════════════════════════════
# GESTÃO DE AUTOMS (Mensagens Automáticas)
# ══════════════════════════════════════════════

def load_automs():
    return safe_json_load(AUTOMS_FILE, [])

def save_automs(automs):
    safe_json_save(AUTOMS_FILE, automs)

def add_autom(title, message):
    automs = load_automs()
    automs.append({
        "title": title or "",
        "message": message or "",
        "ativa": True,
        "criada_em": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })
    save_automs(automs)
    return len(automs)

def remove_autom(index):
    automs = load_automs()
    if 0 <= index < len(automs):
        removed = automs.pop(index)
        save_automs(automs)
        return removed
    return None

def toggle_autom(index):
    automs = load_automs()
    if 0 <= index < len(automs):
        automs[index]["ativa"] = not automs[index].get("ativa", True)
        save_automs(automs)
        return automs[index]
    return None

def update_autom(index, title=None, message=None):
    automs = load_automs()
    if 0 <= index < len(automs):
        if title is not None:
            automs[index]["title"] = title
        if message is not None:
            automs[index]["message"] = message
        save_automs(automs)
        return automs[index]
    return None

# ══════════════════════════════════════════════
# MENSAGENS PRONTAS (pré-configuradas)
# ══════════════════════════════════════════════

def load_msgs_prontas():
    return safe_json_load(MSGS_PRONTAS_FILE, [])

def save_msgs_prontas(msgs):
    safe_json_save(MSGS_PRONTAS_FILE, msgs)

def add_msg_pronta(title, message):
    msgs = load_msgs_prontas()
    msgs.append({
        "title": title or "",
        "message": message or "",
        "ativa": True,
        "criada_em": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })
    save_msgs_prontas(msgs)
    return len(msgs)

def remove_msg_pronta(index):
    msgs = load_msgs_prontas()
    if 0 <= index < len(msgs):
        removed = msgs.pop(index)
        save_msgs_prontas(msgs)
        return removed
    return None

def toggle_msg_pronta(index):
    msgs = load_msgs_prontas()
    if 0 <= index < len(msgs):
        msgs[index]["ativa"] = not msgs[index].get("ativa", True)
        save_msgs_prontas(msgs)
        return msgs[index]
    return None

def update_msg_pronta(index, title=None, message=None):
    msgs = load_msgs_prontas()
    if 0 <= index < len(msgs):
        if title is not None:
            msgs[index]["title"] = title
        if message is not None:
            msgs[index]["message"] = message
        save_msgs_prontas(msgs)
        return msgs[index]
    return None

# ══════════════════════════════════════════════
# AUTO-REPLY (Resposta automática em DM)
# ══════════════════════════════════════════════

def load_autoreply():
    data = safe_json_load(AUTOREPLY_FILE, {"ativo": False, "mensagem": ""})
    if isinstance(data, list):
        data = {"ativo": False, "mensagem": ""}
        safe_json_save(AUTOREPLY_FILE, data)
    return data

def save_autoreply(data):
    safe_json_save(AUTOREPLY_FILE, data)

def set_autoreply(ativo, mensagem=None):
    data = load_autoreply()
    data["ativo"] = ativo
    if mensagem is not None:
        data["mensagem"] = mensagem
    save_autoreply(data)
    return data

# Track quem já recebeu auto-reply nesta sessão
autoreply_sent = set()

# ══════════════════════════════════════════════
# ESTADO PER-USER (edição, envio, etc.)
# ══════════════════════════════════════════════

edit_states = {}

# ══════════════════════════════════════════════
# SESSION MANAGER (Painel IPTV)
# ══════════════════════════════════════════════

class SessionManager:
    def __init__(self):
        self._sessions = {}
        self._states = {}
        self._cache = {}
        self._pagination = {}

    def get_session(self, uid):
        entry = self._sessions.get(uid)
        if not entry:
            return None
        if time.time() - entry["login_time"] > SESSION_TIMEOUT:
            self.logout(uid)
            return None
        return entry["session"]

    def get_username(self, uid):
        entry = self._sessions.get(uid)
        return entry["username"] if entry else "Conta"

    def set_session(self, uid, session, username):
        self._sessions[uid] = {"session": session, "username": username, "login_time": time.time()}

    def logout(self, uid):
        for store in (self._sessions, self._states, self._cache, self._pagination):
            store.pop(uid, None)

    def set_state(self, uid, step, data=None):
        self._states[uid] = {"step": step, "data": data or {}}

    def get_state(self, uid):
        return self._states.get(uid)

    def clear_state(self, uid):
        self._states.pop(uid, None)

    def get_cache(self, uid, key):
        entry = self._cache.get(uid, {}).get(key)
        if entry and time.time() - entry["time"] < CACHE_TTL:
            return entry["data"]
        return None

    def set_cache(self, uid, key, data):
        self._cache.setdefault(uid, {})[key] = {"data": data, "time": time.time()}

    def clear_cache(self, uid):
        self._cache.pop(uid, None)

    def set_page_data(self, uid, items, list_type):
        self._pagination[uid] = {"items": items, "type": list_type}

    def get_page_data(self, uid):
        return self._pagination.get(uid)

sm = SessionManager()

# ══════════════════════════════════════════════
# API DO PAINEL (vendedorp2p.com)
# ══════════════════════════════════════════════

class PainelAPI:
    @staticmethod
    def _url(path):
        return urljoin(PAINEL_URL, path)

    @staticmethod
    def _csrf(session, url):
        try:
            soup = BeautifulSoup(session.get(url, timeout=10).text, "html.parser")
            tag = soup.find("input", {"name": "csrf_token"})
            return tag["value"] if tag else ""
        except Exception:
            return ""

    @staticmethod
    def _parse_response(html_text):
        """Extrai dados da resposta HTML do painel."""
        info = {}
        try:
            soup = BeautifulSoup(html_text, "html.parser")

            # Alertas de sucesso
            for cls in ["alert-success", "alert", "success", "result"]:
                div = soup.find("div", class_=re.compile(cls, re.I))
                if div:
                    info["message"] = div.get_text(strip=True)[:200]
                    break

            # Codigo/textarea
            for tag in soup.find_all(["code", "pre", "textarea"]):
                text = tag.get_text(strip=True)
                if text:
                    info["raw_data"] = text[:500]

            # Inputs com valores
            for inp in soup.find_all("input"):
                name = inp.get("name", inp.get("id", ""))
                val = inp.get("value", "")
                if val and name and name != "csrf_token":
                    info[name] = val

            # URLs de acesso (m3u, player_api, etc)
            url_patterns = re.findall(
                r'(https?://[^\s<>"\']+(?:\.m3u|/get\.php|/player_api\.php|/c/|/live/)[^\s<>"\']*)',
                html_text
            )
            if url_patterns:
                info["urls"] = list(set(url_patterns))

            # DNS/Host/Port
            dns = re.search(r'(?:dns|host|server)[:\s]+([a-zA-Z0-9._-]+\.[a-z]{2,})', html_text, re.I)
            if dns:
                info["dns"] = dns.group(1)
            port = re.search(r'(?:port|porta)[:\s]+(\d{2,5})', html_text, re.I)
            if port:
                info["port"] = port.group(1)

            # Username/Password extraidos
            user = re.search(r'(?:username|user)[:\s]+([^\s<>"\']+)', html_text, re.I)
            if user and "username" not in info:
                info["username"] = user.group(1)
            pw = re.search(r'(?:password|pass|senha)[:\s]+([^\s<>"\']+)', html_text, re.I)
            if pw and "password" not in info:
                info["password"] = pw.group(1)

            # Expiracao
            exp = re.search(r'(?:exp|expir|validade)[:\s]+([\d]{4}-[\d]{2}-[\d]{2})', html_text, re.I)
            if exp:
                info["exp_date"] = exp.group(1)

            # Dados de tabelas
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        val = cells[1].get_text(strip=True)
                        if val and key:
                            clean = re.sub(r'[^a-z_]', '', key.replace(' ', '_'))
                            if clean and clean not in info:
                                info[clean] = val

        except Exception:
            pass
        return info

    @staticmethod
    def login(username, password):
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0 (Linux; Android 13)"})
        try:
            r = s.get(PainelAPI._url("/login/"), timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            csrf = soup.find("input", {"name": "csrf_token"})
            if not csrf:
                return None, "CSRF nao encontrado"
            s.post(PainelAPI._url("/login/"), data={
                "try_login": "1", "csrf_token": csrf["value"],
                "username": username, "password": password
            }, timeout=15)
            dash = s.get(PainelAPI._url("/dashboard/api?get_info&month=0"), timeout=10)
            if dash.status_code != 200:
                return None, "Credenciais invalidas"
            return s, dash.json()
        except requests.Timeout:
            return None, "Timeout"
        except Exception as e:
            return None, str(e)[:80]

    @staticmethod
    def dashboard(s):
        try:
            return s.get(PainelAPI._url("/dashboard/api?get_info&month=0"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def stats(s):
        try:
            return s.get(PainelAPI._url("/dashboard/api/?get_stats"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def sales(s):
        try:
            return s.get(PainelAPI._url("/dashboard/api/?get_sales"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def credits(s):
        try:
            return s.post(PainelAPI._url("/api/get_credits/"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def iptv_clients(s):
        try:
            return s.get(PainelAPI._url("/clients/api/?get_clients"), timeout=15).json().get("clients", [])
        except Exception:
            return []

    @staticmethod
    def p2p_clients(s):
        try:
            return s.get(PainelAPI._url("/p2p/api/?get_clients"), timeout=15).json().get("clients", [])
        except Exception:
            return []

    @staticmethod
    def search_client(s, q):
        try:
            return s.get(PainelAPI._url(f"/clients/api/?search_client={q}"), timeout=10).json().get("clients", [])
        except Exception:
            return []

    @staticmethod
    def search_p2p(s, q):
        try:
            return s.get(PainelAPI._url(f"/p2p/api/?search_client={q}"), timeout=10).json().get("clients", [])
        except Exception:
            return []

    @staticmethod
    def get_client(s, cid):
        try:
            return s.get(PainelAPI._url(f"/clients/api/?get_client&id={cid}"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_bouquets(s):
        try:
            return s.get(PainelAPI._url("/clients/api/?get_bouquets"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_packages(s):
        try:
            return s.get(PainelAPI._url("/clients/api/?get_packages"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def create_iptv(s, user, pw, bouquet, exp):
        try:
            url = PainelAPI._url("/clients/create/")
            csrf = PainelAPI._csrf(s, url)
            r = s.post(url, data={
                "csrf_token": csrf, "username": user, "password": pw,
                "bouquet": bouquet, "exp_date": exp, "create_client": "1"
            }, timeout=15)
            parsed = PainelAPI._parse_response(r.text)
            parsed["_input_username"] = user
            parsed["_input_password"] = pw
            parsed["_input_bouquet"] = bouquet
            parsed["_input_exp"] = exp
            ok = r.status_code == 200 and "error" not in r.text.lower()[:200]
            return ok, parsed
        except Exception as e:
            return False, {"error": str(e)[:80]}

    @staticmethod
    def create_p2p(s, user, pw, exp):
        try:
            url = PainelAPI._url("/p2p/create/")
            csrf = PainelAPI._csrf(s, url)
            r = s.post(url, data={
                "csrf_token": csrf, "username": user, "password": pw,
                "exp_date": exp, "create_client": "1"
            }, timeout=15)
            parsed = PainelAPI._parse_response(r.text)
            parsed["_input_username"] = user
            parsed["_input_password"] = pw
            parsed["_input_exp"] = exp
            ok = r.status_code == 200 and "error" not in r.text.lower()[:200]
            return ok, parsed
        except Exception as e:
            return False, {"error": str(e)[:80]}

    @staticmethod
    def create_reseller(s, user, pw, creds):
        try:
            url = PainelAPI._url("/resellers/create/")
            csrf = PainelAPI._csrf(s, url)
            r = s.post(url, data={
                "csrf_token": csrf, "username": user, "password": pw,
                "credits": creds, "create_reseller": "1"
            }, timeout=15)
            parsed = PainelAPI._parse_response(r.text)
            parsed["_input_username"] = user
            parsed["_input_password"] = pw
            parsed["_input_credits"] = creds
            ok = r.status_code == 200 and "error" not in r.text.lower()[:200]
            return ok, parsed
        except Exception as e:
            return False, {"error": str(e)[:80]}

    @staticmethod
    def edit_client(s, ctype, cid, data_dict):
        try:
            path = f"/clients/edit/{cid}" if ctype == "iptv" else f"/p2p/edit/{cid}"
            url = PainelAPI._url(path)
            csrf = PainelAPI._csrf(s, url)
            data_dict.update({"csrf_token": csrf, "edit_client": "1"})
            return s.post(url, data=data_dict, timeout=10).status_code == 200
        except Exception:
            return False

    @staticmethod
    def delete_client(s, ctype, cid):
        try:
            path = f"/clients/delete/{cid}" if ctype == "iptv" else f"/p2p/delete/{cid}"
            return s.get(PainelAPI._url(path), timeout=10).status_code == 200
        except Exception:
            return False

    @staticmethod
    def delete_reseller(s, rid):
        try:
            return s.get(PainelAPI._url(f"/resellers/delete/{rid}"), timeout=10).status_code == 200
        except Exception:
            return False

    @staticmethod
    def resellers(s):
        try:
            return s.get(PainelAPI._url("/clients/api/?get_allowed_resellers"), timeout=10).json().get("resellers", [])
        except Exception:
            return []

    @staticmethod
    def connections(s):
        try:
            return s.get(PainelAPI._url("/connections/api/?get_connections"), timeout=10).json().get("connections", [])
        except Exception:
            return []

    @staticmethod
    def fast_message(s, cid):
        try:
            return s.get(PainelAPI._url(f"/clients/api/?fast_message&client_id={cid}"), timeout=10).status_code == 200
        except Exception:
            return False

    @staticmethod
    def test(s, ttype):
        urls = {
            "iptv1": "/test/fast_client/1", "iptv2": "/test/fast_client/2",
            "p2p1": "/test/fast_p2p/1", "p2p2": "/test/fast_p2p/2",
        }
        labels = {"iptv1": "IPTV 24h", "iptv2": "IPTV 48h", "p2p1": "P2P 24h", "p2p2": "P2P 48h"}
        try:
            r = s.get(PainelAPI._url(urls[ttype]), timeout=15)
            parsed = PainelAPI._parse_response(r.text)
            parsed["_test_type"] = labels.get(ttype, ttype)

            # Tentar JSON
            try:
                j = r.json()
                if isinstance(j, dict):
                    for k, v in j.items():
                        if k not in parsed:
                            parsed[k] = v
            except Exception:
                pass

            # Fallback: texto limpo
            if len(parsed) <= 1:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                clean = soup.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in clean.split("\n") if l.strip() and len(l.strip()) > 2]
                parsed["_raw_lines"] = lines[:20]

            return parsed
        except Exception as e:
            return {"error": str(e)[:80]}

    @staticmethod
    def logs(s, ltype):
        urls = {"login": "/logs/login/", "clients": "/logs/clients/",
                "resellers": "/logs/resellers/", "sales": "/logs/sales/"}
        try:
            soup = BeautifulSoup(s.get(PainelAPI._url(urls[ltype]), timeout=10).text, "html.parser")
            table = soup.find("table")
            if not table:
                return []
            results = []
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cells:
                    if headers and len(headers) == len(cells):
                        results.append(dict(zip(headers, cells)))
                    else:
                        results.append({"data": " | ".join(cells)})
            return results
        except Exception:
            return []

    @staticmethod
    def get_clients_online(s):
        try:
            return s.get(PainelAPI._url("/api/get_clients_online"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_servers(s):
        try:
            return s.get(PainelAPI._url("/api/get_servers"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_devices(s):
        try:
            return s.get(PainelAPI._url("/api/get_devices"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_user_info_api(s):
        try:
            return s.get(PainelAPI._url("/api/get_user_info"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_statistics(s):
        try:
            return s.get(PainelAPI._url("/api/get_statistics"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_notifications(s):
        try:
            return s.get(PainelAPI._url("/api/get_notifications"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_sales_today(s):
        try:
            return s.get(PainelAPI._url("/api/get_sales_today"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_sales_month(s):
        try:
            return s.get(PainelAPI._url("/api/get_sales_month"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def get_dashboard_connections(s):
        try:
            return s.get(PainelAPI._url("/dashboard/api/?get_connections"), timeout=10).json()
        except Exception:
            return None

    @staticmethod
    def edit_reseller(s, rid, data_dict):
        try:
            url = PainelAPI._url(f"/resellers/edit/{rid}")
            csrf = PainelAPI._csrf(s, url)
            data_dict.update({"csrf_token": csrf, "edit_reseller": "1"})
            return s.post(url, data=data_dict, timeout=10).status_code == 200
        except Exception:
            return False

# ══════════════════════════════════════════════
# FORMATADOR DE RESULTADOS DO PAINEL
# ══════════════════════════════════════════════

def format_panel_result(info, title, emoji):
    """Formata dados criados/teste de forma limpa e profissional."""
    t = f"{emoji} **{title}**\n{LINE}\n\n"

    # Campos de entrada do usuario
    input_map = {
        "_input_username": f"{E['user']} Usuario",
        "_input_password": f"{E['pass']} Senha",
        "_input_bouquet": f"{E['tv']} Bouquet",
        "_input_exp": f"{E['time']} Expiracao",
        "_input_credits": f"{E['credit']} Creditos",
    }
    has_input = False
    for key, label in input_map.items():
        if key in info:
            t += f"{label}: `{info[key]}`\n"
            has_input = True

    # Campos extraidos do painel
    extract_map = {
        "username": f"{E['user']} Usuario",
        "password": f"{E['pass']} Senha",
        "dns": f"{E['dns']} DNS/Host",
        "port": f"{E['port']} Porta",
        "exp_date": f"{E['time']} Expiracao",
    }
    has_ext = False
    for key, label in extract_map.items():
        if key in info and not key.startswith("_input"):
            val = info[key]
            if val and str(val).strip():
                if not has_ext and has_input:
                    t += f"\n{THIN}\n{E['info']} **Dados do Painel:**\n\n"
                t += f"{label}: `{val}`\n"
                has_ext = True

    # URLs
    if "urls" in info and info["urls"]:
        t += f"\n{E['link']} **URLs de Acesso:**\n"
        for url in info["urls"][:5]:
            t += f"```\n{url}\n```\n"

    # Raw lines
    if "_raw_lines" in info and info["_raw_lines"]:
        t += f"\n{E['info']} **Informacoes:**\n"
        for line in info["_raw_lines"][:10]:
            if line and not line.isspace():
                t += f"  - {line}\n"

    # Raw data
    if "raw_data" in info:
        t += f"\n{E['copy']} **Dados:**\n```\n{info['raw_data'][:400]}\n```\n"

    # Campos extras
    skip = set(list(input_map.keys()) + list(extract_map.keys()) +
               ["urls", "_raw_lines", "raw_data", "message", "error", "_test_type", "csrf_token"])
    extra = {k: v for k, v in info.items() if k not in skip and v and str(v).strip()}
    if extra:
        t += f"\n{E['info']} **Detalhes:**\n"
        for k, v in list(extra.items())[:10]:
            t += f"  {k.replace('_',' ').title()}: `{v}`\n"

    if "message" in info:
        t += f"\n{E['check']} {info['message']}\n"

    t += f"\n{LINE}"
    return t

# ══════════════════════════════════════════════
# UI DO PAINEL
# ══════════════════════════════════════════════

class PainelUI:
    @staticmethod
    def dash_text(username, creds, dash):
        cr = creds.get("credits", "N/A") if creds else "N/A"
        iptv = dash.get("iptv", {}) if dash else {}
        p2p = dash.get("p2p", {}) if dash else {}
        return (
            f"{E['crown']} **SILVA IPTV MANAGER** `v{BOT_VERSION}`\n{LINE}\n\n"
            f"{E['user']} Logado: `{username}`\n"
            f"{E['credit']} Creditos: `{cr}`\n\n"
            f"{E['tv']} **IPTV** — Ativos: `{iptv.get('active_clients_count', 0)}` | Online: `{iptv.get('online_clients_count', 0)}`\n"
            f"{E['p2p']} **P2P** — Ativos: `{p2p.get('active_clients_count', 0)}` | Online: `{p2p.get('online_clients_count', 0)}`\n\n"
            f"{LINE}"
        )

    @staticmethod
    def main_menu():
        return [
            [Button.inline(f"{E['tv']} IPTV", b"panel_iptv_list"), Button.inline(f"{E['p2p']} P2P", b"panel_p2p_list")],
            [Button.inline(f"{E['rev']} Revendas", b"panel_resellers"), Button.inline(f"{E['conn']} Conexoes", b"panel_connections")],
            [Button.inline(f"{E['create']} Criar IPTV", b"panel_create_iptv"), Button.inline(f"{E['create']} Criar P2P", b"panel_create_p2p")],
            [Button.inline(f"{E['create']} Criar Revenda", b"panel_create_rev"), Button.inline(f"{E['test']} Testes", b"panel_tests")],
            [Button.inline(f"{E['search']} Buscar", b"panel_search"), Button.inline(f"{E['fast']} Fast Msg", b"panel_fast_msg")],
            [Button.inline(f"{E['log']} Logs", b"panel_logs"), Button.inline(f"{E['dash']} Dashboard", b"panel_dash")],
            [Button.inline(f"{E['tool']} Ferramentas", b"panel_tools"), Button.inline(f"{E['exit']} Sair", b"panel_logout")],
        ]

    @staticmethod
    def back():
        return [[Button.inline(f"{E['back']} Menu Painel", b"panel_menu")]]

    @staticmethod
    def cancel():
        return [[Button.inline(f"{E['cancel']} Cancelar", b"panel_menu")]]

    @staticmethod
    def confirm(callback_data):
        return [
            [Button.inline(f"{E['ok']} Confirmar", callback_data),
             Button.inline(f"{E['cancel']} Cancelar", b"panel_menu")]
        ]

    @staticmethod
    def client_list(clients, page, emoji, title, prefix):
        total = len(clients)
        pages = max(1, math.ceil(total / PAGE_SIZE))
        page = min(page, pages - 1)
        start = page * PAGE_SIZE
        chunk = clients[start:start + PAGE_SIZE]
        t = f"{emoji} **{title}** — `{total}` total\n{LINE}\n\n"
        if not chunk:
            t += f"{E['warn']} Lista vazia.\n"
        else:
            for i, c in enumerate(chunk, start + 1):
                un = c.get("username", "?")
                st = f"{E['online']}" if c.get("online") else f"{E['offline']}"
                exp = c.get("exp_date", "N/A")
                t += f"`{i}.` {st} `{un}` — Exp: `{exp}`\n"
        t += f"\n{THIN}\n📄 Pag `{page + 1}/{pages}`\n{LINE}"
        btns = []
        for c in chunk:
            cid = str(c.get("id", ""))
            un = c.get("username", "?")[:18]
            btns.append([Button.inline(f"{E['info']} {un}", f"panel_det_{prefix}_{cid}".encode())])
        nav = []
        if page > 0:
            nav.append(Button.inline(f"{E['left']}", f"panel_{prefix}_pg_{page - 1}".encode()))
        nav.append(Button.inline(f"{page + 1}/{pages}", b"noop"))
        if page < pages - 1:
            nav.append(Button.inline(f"{E['right']}", f"panel_{prefix}_pg_{page + 1}".encode()))
        if nav:
            btns.append(nav)
        btns.append([Button.inline(f"{E['back']} Menu Painel", b"panel_menu")])
        return t, btns

# ══════════════════════════════════════════════
# FUNÇÕES DE CONSULTA IPTV / URL (check_url)
# ══════════════════════════════════════════════

def format_date(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%d/%m/%Y %H:%M:%S')
    except Exception:
        return "N/D"

def fetch_data(session, url):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Linux; Android 10)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6)",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)"
    ]
    headers = {'User-Agent': random.choice(user_agents)}
    try:
        response = session.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def is_port_open(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            return sock.connect_ex((host, port)) == 0
    except socket.error:
        return False

def get_host_ip(host):
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None

def check_url(url):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port or 80
    query_params = parse_qs(parsed_url.query)
    username = query_params.get('username', [None])[0]
    password = query_params.get('password', [None])[0]

    if not (host and username and password):
        return None, "❌ URL inválida. Faltam parâmetros (username/password)."

    ip_address = get_host_ip(host)
    if not ip_address:
        return None, f"❌ Não foi possível resolver o host."

    if not is_port_open(host, port):
        return None, f"❌ Servidor offline."

    api_url = f'http://{host}:{port}/player_api.php?username={username}&password={password}'

    try:
        with Session() as session:
            data = fetch_data(session, api_url)
            if not data:
                return None, "❌ Servidor OFF ou sem resposta."

            user_info = data.get('user_info', {})
            if user_info.get('auth') == 0:
                return None, "❌ Credenciais inválidas (auth=0)."

            live = fetch_data(session, f'{api_url}&action=get_live_streams')
            vod = fetch_data(session, f'{api_url}&action=get_vod_streams')
            series = fetch_data(session, f'{api_url}&action=get_series')

            total_canais = len(live) if live else 0
            total_vods = len(vod) if vod else 0
            total_series = len(series) if series else 0

            return build_result(data, total_canais, total_vods, total_series, ip_address), None

    except Exception as e:
        return None, f"❌ Erro: {str(e)}"

def build_result(data, total_canais, total_vods, total_series, ip_address):
    ui = data['user_info']
    si = data['server_info']
    server = si.get('url', 'N/D')
    port = si.get('port', 'N/D')
    username = ui.get('username', 'N/D')
    password = ui.get('password', 'N/D')
    status = ui.get('status', 'N/D')
    creation = format_date(ui.get('created_at', 0))
    expiration = format_date(ui.get('exp_date', 0))
    max_conn = ui.get('max_connections', 'N/D')
    active_conn = ui.get('active_cons', 'N/D')
    formats = ', '.join(ui.get('allowed_output_formats', []))
    timezone = si.get('timezone', 'N/D')
    https_port = si.get('https_port', 'N/D')
    protocol = si.get('server_protocol', 'N/D')
    rtmp_port = si.get('rtmp_port', 'N/D')
    time_now = si.get('time_now', 'N/D')

    status_emoji = "✅" if status == "Active" else "❌"
    m3u_link = f"http://{server}:{port}/get.php?username={username}&password={password}&type=m3u"

    result = (
        f"╔══════════════════════════════╗\n"
        f"║   {status_emoji} RESULTADO DA CONSULTA     ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Status:** `{status}`\n"
        f"👤 **Usuário:** `{username}`\n"
        f"🔑 **Senha:** `{password}`\n"
        f"\n"
        f"📅 **Criação:** `{creation}`\n"
        f"⏰ **Expiração:** `{expiration}`\n"
        f"\n"
        f"🔗 **Conexões:** `{active_conn}/{max_conn}`\n"
        f"\n"
        f"🌐 **Host:** `{server}`\n"
        f"🔌 **Porta:** `{port}`\n"
        f"📡 **IP:** `{ip_address}`\n"
        f"🔒 **HTTPS:** `{https_port}`\n"
        f"📶 **Protocolo:** `{protocol}`\n"
        f"📺 **RTMP:** `{rtmp_port}`\n"
        f"🕐 **Hora:** `{time_now}`\n"
        f"🌍 **Timezone:** `{timezone}`\n"
        f"\n"
        f"📂 **Formato:** `{formats}`\n"
        f"📺 **Canais:** `{total_canais}`\n"
        f"🎬 **Filmes:** `{total_vods}`\n"
        f"🎭 **Séries:** `{total_series}`\n"
        f"\n"
        f"🔗 **M3U:**\n`{m3u_link}`\n"
        f"\n"
        f"╚══════════════════════════════╝"
    )
    return result

# ══════════════════════════════════════════════
#  USERBOT — AUTO-REPLY EM DMs
# ══════════════════════════════════════════════

@userbot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_dm_autoreply(event):
    """Responde automaticamente quando alguém inicia DM."""
    if event.sender_id == OWNER_ID:
        return

    ar = load_autoreply()
    if not ar.get("ativo") or not ar.get("mensagem"):
        return

    if event.sender_id in autoreply_sent:
        return

    autoreply_sent.add(event.sender_id)

    sender = await event.get_sender()
    register_user(
        event.sender_id,
        getattr(sender, 'first_name', '') or '',
        getattr(sender, 'last_name', '') or '',
        getattr(sender, 'username', None)
    )

    await event.reply(ar["mensagem"], parse_mode='md')

# ══════════════════════════════════════════════
#  USERBOT — CONSULTA VIA REPLY (URL)
# ══════════════════════════════════════════════

URL_PATTERN = r'(https?://[^\s]+)'

@userbot.on(events.NewMessage(incoming=True))
async def handle_incoming_reply(event):
    """Responde consultas quando alguém responde a uma mensagem do userbot com URL."""
    if not event.is_reply:
        return

    replied = await event.get_reply_message()
    if not replied or not replied.out:
        return

    if event.is_group or event.is_channel:
        if not is_group_allowed(event.chat_id):
            return

    match = re.search(URL_PATTERN, event.raw_text)
    if not match:
        return

    url = match.group(1)
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', '') or ''
    sender_last = getattr(sender, 'last_name', '') or ''
    sender_username = getattr(sender, 'username', None)
    sender_id = sender.id

    register_user(sender_id, sender_name, sender_last, sender_username)

    processing_msg = await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║    ⏳ PROCESSANDO CONSULTA    ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"👤 **Solicitante:** {sender_name} {sender_last}\n"
        f"🆔 **ID:** `{sender_id}`\n"
        f"📡 Aguarde..."
    )

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        await processing_msg.edit(
            f"╔══════════════════════════════╗\n"
            f"║     ❌ CONSULTA FALHOU        ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n"
            f"👤 **Solicitante:** {sender_name} {sender_last}\n"
            f"🆔 **ID:** `{sender_id}`\n"
            f"\n{error}"
        )
        return

    user_tag = f"@{sender_username}" if sender_username else f"`{sender_id}`"
    header = (
        f"👤 **Solicitante:** {sender_name} {sender_last}\n"
        f"🆔 **ID:** `{sender_id}`\n"
        f"📎 **User:** {user_tag}\n\n"
    )

    await processing_msg.edit(header + result, parse_mode='md')

    try:
        channel_msg = (
            f"📨 **Nova Consulta**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} {sender_last} ({user_tag})\n"
            f"🆔 **ID:** `{sender_id}`\n"
            f"💬 **Chat:** `{event.chat_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"\n{result}"
        )
        await userbot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal: {e}")

@userbot.on(events.NewMessage(outgoing=True))
async def handle_self_reply(event):
    """Permite o próprio dono consultar respondendo suas próprias mensagens com URL."""
    if not event.is_reply:
        return

    replied = await event.get_reply_message()
    if not replied or not replied.out:
        return

    if "RESULTADO DA CONSULTA" in event.raw_text or "PROCESSANDO" in event.raw_text:
        return

    match = re.search(URL_PATTERN, event.raw_text)
    if not match:
        return

    url = match.group(1)
    me = await userbot.get_me()

    processing_msg = await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║    ⏳ PROCESSANDO (TESTE)     ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"👤 **Dono:** {me.first_name or ''}\n"
        f"📡 Aguarde..."
    )

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        await processing_msg.edit(
            f"╔══════════════════════════════╗\n"
            f"║     ❌ CONSULTA FALHOU        ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n{error}"
        )
        return

    me_tag = f"@{me.username}" if me.username else f"`{me.id}`"
    header = (
        f"👤 **Dono:** {me.first_name or ''}\n"
        f"🆔 **ID:** `{me.id}`\n\n"
    )

    await processing_msg.edit(header + result, parse_mode='md')

    try:
        channel_msg = (
            f"📨 **Consulta (Teste Próprio)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Dono:** {me.first_name or ''} ({me_tag})\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"\n{result}"
        )
        await userbot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal: {e}")

# ══════════════════════════════════════════════
#  USERBOT — CONSULTA VIA @InforUser_Bot + URL
# ══════════════════════════════════════════════

@userbot.on(events.NewMessage(incoming=True))
async def handle_bot_mention_query(event):
    """Detecta @InforUser_Bot + URL no chat e faz a consulta via userbot."""
    if event.is_private:
        return

    text = event.raw_text or ""
    mention_pattern = r'@InforUser_Bot\s+(https?://[^\s]+)'
    match = re.search(mention_pattern, text, re.IGNORECASE)
    if not match:
        return

    if not is_group_allowed(event.chat_id):
        return

    url = match.group(1)
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', '') or ''
    sender_last = getattr(sender, 'last_name', '') or ''
    sender_username = getattr(sender, 'username', None)
    sender_id = sender.id

    register_user(sender_id, sender_name, sender_last, sender_username)

    processing_msg = await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║    ⏳ CONSULTANDO URL...       ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"👤 **Solicitante:** {sender_name} {sender_last}\n"
        f"🆔 **ID:** `{sender_id}`\n"
        f"📡 Aguarde...",
        parse_mode='md'
    )

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        await processing_msg.edit(
            f"╔══════════════════════════════╗\n"
            f"║     ❌ CONSULTA FALHOU        ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n"
            f"👤 {sender_name} {sender_last}\n"
            f"🆔 `{sender_id}`\n"
            f"\n{error}",
            parse_mode='md'
        )
        return

    user_tag = f"@{sender_username}" if sender_username else f"`{sender_id}`"
    header = (
        f"👤 **Solicitante:** {sender_name} {sender_last}\n"
        f"🆔 **ID:** `{sender_id}`\n"
        f"📎 **User:** {user_tag}\n\n"
    )

    await processing_msg.edit(header + result, parse_mode='md')

    try:
        channel_msg = (
            f"📨 **Consulta via @InforUser\_Bot (Userbot)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} {sender_last} ({user_tag})\n"
            f"🆔 **ID:** `{sender_id}`\n"
            f"💬 **Chat:** `{event.chat_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"\n{result}"
        )
        await userbot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal (mention): {e}")

# ══════════════════════════════════════════════
#  BOT — GESTÃO DE GRUPOS (com paginação)
# ══════════════════════════════════════════════

def build_groups_page(page=0):
    groups = load_groups()
    total = len(groups)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_groups = groups[start:end]

    text = (
        f"╔══════════════════════════════╗\n"
        f"║   📋 GRUPOS PERMITIDOS        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Total:** `{total}` grupo(s)\n"
        f"📄 **Página:** `{page + 1}/{total_pages}`\n\n"
    )

    if not page_groups:
        text += "📭 Nenhum grupo cadastrado.\n"
    else:
        for i, g in enumerate(page_groups, start=start + 1):
            text += f"**{i}.** `{g['id']}` — {g['name']}\n"

    text += f"\n╚══════════════════════════════╝"

    buttons = []
    for g in page_groups:
        buttons.append([Button.inline(f"🗑 Remover: {g['name'][:20]}", data=f"rmgrp:{g['id']}")])

    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("◀️ Voltar", data=f"grppage:{page - 1}"))
    nav_row.append(Button.inline(f"📄 {page + 1}/{total_pages}", data="noop"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Avançar ▶️", data=f"grppage:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        Button.inline("➕ Adicionar Grupo", data="addgrp"),
        Button.inline("🔄 Atualizar", data="grppage:0")
    ])

    return text, buttons

# ══════════════════════════════════════════════
#  BOT — /start (Menu Unificado)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/start$'))
async def bot_start(event):
    if event.is_private:
        sender = await event.get_sender()
        register_user(
            event.sender_id,
            getattr(sender, 'first_name', '') or '',
            getattr(sender, 'last_name', '') or '',
            getattr(sender, 'username', None)
        )

        is_owner = event.sender_id == OWNER_ID

        # Verifica se já está logado no painel
        panel_session = sm.get_session(event.sender_id)

        text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  {E['crown']} SILVA MANAGER PRO v{BOT_VERSION}     ║\n"
            f"╚══════════════════════════════════════╝\n"
            f"\n"
            f"Bem-vindo! Sistema **completo** de gerenciamento.\n\n"
            f"📡 **Consulta URL:** Envie uma URL aqui\n"
            f"📡 **Inline:** `@InforUser_Bot URL`\n"
            f"📋 **Comandos:** /help\n"
        )

        if panel_session:
            text += f"\n{E['ok']} **Painel conectado:** `{sm.get_username(event.sender_id)}`\n"
        else:
            text += f"\n{E['lock']} Use /painel para acessar o painel IPTV\n"

        if is_owner:
            text += f"\n{E['crown']} **Painel Admin disponível!**\n"

        text += "\n╚══════════════════════════════════════╝"

        buttons = []
        if is_owner:
            buttons = [
                [Button.inline(f"{E['lock']} Painel IPTV", data="panel_login_start"),
                 Button.inline("📋 Grupos", data="grppage:0")],
                [Button.inline("💬 AutoMs", data="autompage:0"),
                 Button.inline("📝 Msgs Prontas", data="mppage:0")],
                [Button.inline("🔄 Auto-Reply", data="ar_panel"),
                 Button.inline("👥 Usuários", data="userspage:0")],
                [Button.inline("📊 Status", data="show_status")]
            ]

        await event.reply(text, buttons=buttons if buttons else None, parse_mode='md')
    raise events.StopPropagation

# ══════════════════════════════════════════════
#  BOT — /painel (Login no Painel IPTV)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/painel$'))
async def bot_painel_start(event):
    if not event.is_private:
        return
    uid = event.sender_id
    sm.logout(uid)
    sm.set_state(uid, "panel_login_user")
    try:
        await event.delete()
    except Exception:
        pass
    await event.respond(
        f"{E['lock']} **SILVA IPTV MANAGER** `v{BOT_VERSION}`\n{LINE}\n\n"
        f"Bem-vindo ao painel profissional.\n\n"
        f"{E['user']} Digite seu **usuario** do painel:",
        buttons=PainelUI.cancel(), parse_mode="md"
    )
    raise events.StopPropagation

@bot.on(events.CallbackQuery(data=b"panel_login_start"))
async def panel_login_start_cb(event):
    uid = event.sender_id
    sm.logout(uid)
    sm.set_state(uid, "panel_login_user")
    try:
        await event.delete()
    except Exception:
        pass
    await event.respond(
        f"{E['lock']} **SILVA IPTV MANAGER** `v{BOT_VERSION}`\n{LINE}\n\n"
        f"Bem-vindo ao painel profissional.\n\n"
        f"{E['user']} Digite seu **usuario** do painel:",
        buttons=PainelUI.cancel(), parse_mode="md"
    )

# ══════════════════════════════════════════════
#  BOT — /help
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/help$'))
async def bot_help(event):
    is_owner = (event.sender_id == OWNER_ID)
    text = (
        f"╔══════════════════════════════╗\n"
        f"║   📖 COMANDOS                 ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"🔹 `/start` — Menu inicial\n"
        f"🔹 `/help` — Esta mensagem\n"
        f"🔹 `/painel` — Login no painel IPTV\n"
        f"🔹 Envie uma **URL** no privado para consultar\n"
        f"🔹 **Inline:** `@InforUser_Bot URL`\n"
    )
    if is_owner:
        text += (
            f"\n"
            f"{E['crown']} **COMANDOS ADMIN:**\n"
            f"🔹 `/grupos` — Gestão de grupos\n"
            f"🔹 `/addgrupo <id>` — Adicionar grupo\n"
            f"🔹 `/id` — Ver ID do chat\n"
            f"🔹 `/status` — Status do sistema\n"
            f"🔹 `/automs` — Mensagens automáticas\n"
            f"🔹 `/addautom <titulo> | <msg>` — Add autom\n"
            f"🔹 `/msgprontas` — Msgs pré-configuradas\n"
            f"🔹 `/addmsg <titulo> | <msg>` — Add msg pronta\n"
            f"🔹 `/autoreply` — Auto-reply em DMs\n"
            f"🔹 `/usuarios` — Usuários registrados\n"
            f"🔹 `/broadcast <msg>` — Enviar a todos\n"
            f"🔹 `/painel` — Painel IPTV/P2P\n"
        )
    text += "\n╚══════════════════════════════╝"
    await event.reply(text, parse_mode='md')

# ══════════════════════════════════════════════
#  BOT — GRUPOS
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/grupos$'))
async def bot_grupos(event):
    if event.sender_id != OWNER_ID:
        await event.reply("⛔ Apenas o dono pode gerenciar grupos.")
        return
    text, buttons = build_groups_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^grppage:(\d+)$'))
async def bot_callback_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_groups_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^rmgrp:(-?\d+)$'))
async def bot_callback_remove(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    gid = int(event.pattern_match.group(1))
    removed = remove_group(gid)
    if removed:
        await event.answer(f"✅ Grupo {gid} removido!", alert=True)
    else:
        await event.answer(f"❌ Grupo {gid} não encontrado.", alert=True)
    text, buttons = build_groups_page(0)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^addgrp$'))
async def bot_callback_add_prompt(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    await event.answer()
    await event.reply(
        "╔══════════════════════════════╗\n"
        "║   ➕ ADICIONAR GRUPO          ║\n"
        "╚══════════════════════════════╝\n"
        "\n"
        "Envie apenas o **ID do grupo**:\n"
        "`/addgrupo -100123456`\n"
        "\n💡 O nome será detectado automaticamente.\n"
        "💡 Use `/id` dentro do grupo para descobrir o ID.",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^noop$'))
async def bot_callback_noop(event):
    await event.answer()

@bot.on(events.NewMessage(pattern=r'^/addgrupo\s+(-?\d+)(?:\s+(.+))?$'))
async def bot_add_group(event):
    if event.sender_id != OWNER_ID:
        return
    gid = int(event.pattern_match.group(1))
    name = event.pattern_match.group(2)

    if not name:
        try:
            entity = await bot.get_entity(gid)
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Grupo')
        except Exception:
            name = f"Grupo {gid}"

    name = name.strip()
    added = add_group(gid, name)
    if added:
        await event.reply(
            f"✅ **Grupo adicionado!**\n"
            f"📋 **Nome:** {name}\n"
            f"🆔 **ID:** `{gid}`\n"
            f"\nUse /grupos para ver a lista.",
            parse_mode='md'
        )
    else:
        await event.reply(f"⚠️ Grupo `{gid}` já está cadastrado.", parse_mode='md')

# ══════════════════════════════════════════════
#  BOT — /id, /status
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/id$'))
async def bot_get_id(event):
    chat = await event.get_chat()
    chat_name = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'N/A')
    await event.reply(
        f"🆔 **Chat:** `{event.chat_id}`\n"
        f"📋 **Nome:** {chat_name}\n"
        f"👤 **Seu ID:** `{event.sender_id}`",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'^/status$'))
async def bot_status(event):
    if event.sender_id != OWNER_ID:
        return
    groups = load_groups()
    automs = load_automs()
    users = load_users()
    ar = load_autoreply()
    msgs = load_msgs_prontas()
    active_automs = sum(1 for a in automs if a.get("ativa", True))
    active_msgs = sum(1 for m in msgs if m.get("ativa", True))
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   📊 STATUS DO SISTEMA        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Bot + Userbot + Painel Online**\n"
        f"📋 **Grupos ativos:** `{len(groups)}`\n"
        f"💬 **AutoMs:** `{active_automs}/{len(automs)}`\n"
        f"📝 **Msgs Prontas:** `{active_msgs}/{len(msgs)}`\n"
        f"👥 **Usuários:** `{len(users)}`\n"
        f"🔄 **Auto-Reply:** `{'✅ Ativo' if ar.get('ativo') else '❌ Inativo'}`\n"
        f"🕐 **Hora:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^show_status$'))
async def bot_callback_status(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    groups = load_groups()
    automs = load_automs()
    users = load_users()
    ar = load_autoreply()
    msgs = load_msgs_prontas()
    active_automs = sum(1 for a in automs if a.get("ativa", True))
    active_msgs = sum(1 for m in msgs if m.get("ativa", True))
    await event.answer()
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   📊 STATUS DO SISTEMA        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Bot + Userbot + Painel Online**\n"
        f"📋 **Grupos:** `{len(groups)}`\n"
        f"💬 **AutoMs:** `{active_automs}/{len(automs)}`\n"
        f"📝 **Msgs Prontas:** `{active_msgs}/{len(msgs)}`\n"
        f"👥 **Usuários:** `{len(users)}`\n"
        f"🔄 **Auto-Reply:** `{'✅ Ativo' if ar.get('ativo') else '❌ Inativo'}`\n"
        f"🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  BOT — CONSULTA NO PRIVADO + PAINEL STATE MACHINE
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.raw_text.startswith('/')))
async def bot_private_handler(event):
    """Handler unificado para mensagens privadas: painel states, edição, e consulta URL."""
    sender = await event.get_sender()
    register_user(
        event.sender_id,
        getattr(sender, 'first_name', '') or '',
        getattr(sender, 'last_name', '') or '',
        getattr(sender, 'username', None)
    )

    uid = event.sender_id
    txt = event.raw_text.strip()

    # ── Verifica estado do painel (login, criação, etc.) ──
    panel_state = sm.get_state(uid)
    if panel_state:
        step, data = panel_state["step"], panel_state["data"]

        async def _del():
            try:
                await event.delete()
            except Exception:
                pass

        # LOGIN
        if step == "panel_login_user":
            data["username"] = txt
            sm.set_state(uid, "panel_login_pass", data)
            await _del()
            await event.respond(f"{E['pass']} Digite sua **senha:**", buttons=PainelUI.cancel(), parse_mode="md")
            return

        if step == "panel_login_pass":
            await _del()
            msg = await event.respond(f"{E['load']} Autenticando...", parse_mode="md")
            s, result = PainelAPI.login(data["username"], txt)
            if not s:
                sm.clear_state(uid)
                await msg.edit(f"{E['err']} **Falha:** `{result}`\n\nUse /painel", parse_mode="md")
                return
            sm.set_session(uid, s, data["username"])
            sm.clear_state(uid)
            cr = PainelAPI.credits(s)
            await msg.edit(PainelUI.dash_text(data["username"], cr, result), buttons=PainelUI.main_menu(), parse_mode="md")
            return

        # BUSCA
        if step == "panel_search_term":
            s = sm.get_session(uid)
            if not s:
                return
            sm.clear_state(uid)
            await _del()
            msg = await event.respond(f"{E['load']} Buscando `{txt}`...", parse_mode="md")
            clients = PainelAPI.search_client(s, txt)
            if not clients:
                await msg.edit(f"{E['search']} Nenhum resultado para `{txt}`", buttons=PainelUI.back(), parse_mode="md")
                return
            sm.set_page_data(uid, clients, "search")
            t, b = PainelUI.client_list(clients, 0, E["search"], "Resultados", "search")
            await msg.edit(t, buttons=b, parse_mode="md")
            return

        # FAST MSG
        if step == "panel_fast_msg_id":
            s = sm.get_session(uid)
            if not s:
                return
            sm.clear_state(uid)
            await _del()
            msg = await event.respond(f"{E['load']} Enviando...", parse_mode="md")
            ok = PainelAPI.fast_message(s, txt)
            r = "enviada" if ok else "falhou"
            await msg.edit(f"{E['ok'] if ok else E['err']} Fast Message **{r}** - ID `{txt}`", buttons=PainelUI.back(), parse_mode="md")
            return

        # CRIAR IPTV
        if step == "panel_ci_user":
            data["username"] = txt
            sm.set_state(uid, "panel_ci_pass", data)
            await _del()
            await event.respond(f"{E['pass']} **Senha** do cliente:", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_ci_pass":
            data["password"] = txt
            sm.set_state(uid, "panel_ci_bouquet", data)
            await _del()
            await event.respond(f"{E['tv']} **Bouquet** (ex: `1,2,3`):", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_ci_bouquet":
            data["bouquet"] = txt
            sm.set_state(uid, "panel_ci_exp", data)
            await _del()
            await event.respond(f"{E['time']} **Expiracao** (ex: `2025-12-31`):", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_ci_exp":
            data["expiry"] = txt
            sm.set_state(uid, "panel_ci_confirm", data)
            await _del()
            await event.respond(
                f"{E['create']} **Confirmar IPTV**\n{LINE}\n\n"
                f"{E['user']} `{data['username']}`\n{E['pass']} `{data['password']}`\n"
                f"{E['tv']} `{data['bouquet']}`\n{E['time']} `{data['expiry']}`",
                buttons=PainelUI.confirm(b"panel_ok_iptv"), parse_mode="md"
            )
            return

        # CRIAR P2P
        if step == "panel_cp_user":
            data["username"] = txt
            sm.set_state(uid, "panel_cp_pass", data)
            await _del()
            await event.respond(f"{E['pass']} **Senha:**", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_cp_pass":
            data["password"] = txt
            sm.set_state(uid, "panel_cp_exp", data)
            await _del()
            await event.respond(f"{E['time']} **Expiracao** (ex: `2025-12-31`):", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_cp_exp":
            data["expiry"] = txt
            sm.set_state(uid, "panel_cp_confirm", data)
            await _del()
            await event.respond(
                f"{E['create']} **Confirmar P2P**\n{LINE}\n\n"
                f"{E['user']} `{data['username']}`\n{E['pass']} `{data['password']}`\n"
                f"{E['time']} `{data['expiry']}`",
                buttons=PainelUI.confirm(b"panel_ok_p2p"), parse_mode="md"
            )
            return

        # CRIAR REVENDEDOR
        if step == "panel_cr_user":
            data["username"] = txt
            sm.set_state(uid, "panel_cr_pass", data)
            await _del()
            await event.respond(f"{E['pass']} **Senha:**", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_cr_pass":
            data["password"] = txt
            sm.set_state(uid, "panel_cr_credits", data)
            await _del()
            await event.respond(f"{E['credit']} **Creditos:**", buttons=PainelUI.cancel(), parse_mode="md")
            return
        if step == "panel_cr_credits":
            data["credits"] = txt
            sm.set_state(uid, "panel_cr_confirm", data)
            await _del()
            await event.respond(
                f"{E['create']} **Confirmar Revendedor**\n{LINE}\n\n"
                f"{E['user']} `{data['username']}`\n{E['pass']} `{data['password']}`\n"
                f"{E['credit']} `{data['credits']}`",
                buttons=PainelUI.confirm(b"panel_ok_rev"), parse_mode="md"
            )
            return

        # EDITAR SENHA
        if step == "panel_edit_pw":
            sm.clear_state(uid)
            await _del()
            s = sm.get_session(uid)
            if not s:
                return
            msg = await event.respond(f"{E['load']} Alterando...", parse_mode="md")
            ok = PainelAPI.edit_client(s, data["type"], data["id"], {"password": txt})
            sm.clear_cache(uid)
            await msg.edit(f"{E['ok'] if ok else E['err']} {'Senha alterada!' if ok else 'Falha.'}", buttons=PainelUI.back(), parse_mode="md")
            return

    # ── Verifica estado de edição (automs, msgs prontas, auto-reply) ──
    state = edit_states.get(event.sender_id)
    if state:
        await handle_edit_state(event, state)
        return

    # ── Verifica se é mensagem encaminhada (para identificar usuário) ──
    if event.sender_id == OWNER_ID and event.forward:
        fwd = event.forward
        fwd_id = getattr(fwd, 'sender_id', None) or getattr(fwd, 'from_id', None)
        if fwd_id:
            user = find_user(fwd_id)
            if user:
                await event.reply(
                    f"╔══════════════════════════════╗\n"
                    f"║   👤 USUÁRIO ENCONTRADO       ║\n"
                    f"╚══════════════════════════════╝\n"
                    f"\n"
                    f"👤 **Nome:** {user['nome']}\n"
                    f"🆔 **ID:** `{user['id']}`\n"
                    f"📎 **Username:** @{user.get('username', 'N/A')}\n"
                    f"📅 **Registrado:** `{user.get('registrado_em', 'N/D')}`\n"
                    f"🕐 **Último acesso:** `{user.get('ultimo_acesso', 'N/D')}`\n"
                    f"📊 **Interações:** `{user.get('interacoes', 0)}`\n"
                    f"\n╚══════════════════════════════╝",
                    parse_mode='md'
                )
            else:
                await event.reply(f"❌ Usuário `{fwd_id}` não encontrado no registro.", parse_mode='md')
            return

    # ── Verifica permissão para consulta URL ──
    if event.sender_id == OWNER_ID:
        allowed = True
    else:
        allowed = False
        groups = load_groups()
        for g in groups:
            try:
                participant = await bot(
                    GetParticipantRequest(g["id"], event.sender_id)
                )
                if participant:
                    allowed = True
                    break
            except (UserNotParticipantError, Exception):
                continue

    if not allowed:
        await event.reply(
            "⛔ **Acesso negado.**\n\n"
            f"Você precisa ser membro de um grupo autorizado.\n"
            f"Contato: {OWNER_CONTACT}",
            parse_mode='md'
        )
        return

    # ── Consulta URL ──
    match = re.search(URL_PATTERN, event.raw_text)
    if not match:
        await event.reply(
            "📡 Envie uma **URL** válida para consultar.\n\n"
            "Ou use inline: `@InforUser_Bot URL`",
            parse_mode='md'
        )
        return

    url = match.group(1)
    sender_name = getattr(sender, 'first_name', '') or ''
    sender_last = getattr(sender, 'last_name', '') or ''
    sender_username = getattr(sender, 'username', None)

    processing_msg = await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║    ⏳ PROCESSANDO...          ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n📡 Aguarde...",
        parse_mode='md'
    )

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        await processing_msg.edit(
            f"╔══════════════════════════════╗\n"
            f"║     ❌ CONSULTA FALHOU        ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n{error}",
            parse_mode='md'
        )
        return

    user_tag = f"@{sender_username}" if sender_username else f"`{event.sender_id}`"
    header = (
        f"👤 **Solicitante:** {sender_name} {sender_last}\n"
        f"🆔 **ID:** `{event.sender_id}`\n\n"
    )

    await processing_msg.edit(header + result, parse_mode='md')

    try:
        channel_msg = (
            f"📨 **Consulta (Privado Bot)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} {sender_last} ({user_tag})\n"
            f"🆔 **ID:** `{event.sender_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n{result}"
        )
        await bot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal (privado): {e}")

# ══════════════════════════════════════════════
#  BOT — INLINE MODE
# ══════════════════════════════════════════════

@bot.on(events.InlineQuery)
async def bot_inline_handler(event):
    """Inline: @InforUser_Bot URL"""
    query = event.text.strip()

    if not query:
        builder = event.builder
        article = builder.article(
            title=f"📡 Silva Manager PRO v{BOT_VERSION}",
            description="Digite: @InforUser_Bot URL para consultar",
            text="📡 Use: `@InforUser_Bot URL` para consultar uma URL.",
            parse_mode='md'
        )
        await event.answer([article])
        return

    match = re.search(URL_PATTERN, query)
    if not match:
        builder = event.builder
        article = builder.article(
            title="❌ URL não detectada",
            description="Envie uma URL válida após @InforUser_Bot",
            text="❌ Envie uma URL válida.\nExemplo: `@InforUser_Bot http://...`",
            parse_mode='md'
        )
        await event.answer([article])
        return

    url = match.group(1)

    sender = await event.get_sender()
    register_user(
        event.sender_id,
        getattr(sender, 'first_name', '') or '',
        getattr(sender, 'last_name', '') or '',
        getattr(sender, 'username', None)
    )

    if event.sender_id == OWNER_ID:
        allowed = True
    else:
        allowed = False
        groups = load_groups()
        for g in groups:
            try:
                participant = await bot(
                    GetParticipantRequest(g["id"], event.sender_id)
                )
                if participant:
                    allowed = True
                    break
            except (UserNotParticipantError, Exception):
                continue

    if not allowed:
        await event.answer(
            results=[],
            switch_pm="⛔ Sem permissão. Entre em um grupo autorizado.",
            switch_pm_param="start"
        )
        return

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        builder = event.builder
        article = builder.article(
            title="❌ Consulta Falhou",
            description=error[:100],
            text=error,
            parse_mode='md'
        )
        await event.answer([article])
        return

    builder = event.builder
    article = builder.article(
        title="✅ Resultado da Consulta",
        description="Clique para enviar o resultado",
        text=result,
        parse_mode='md'
    )
    await event.answer([article])

    try:
        sender_name = getattr(sender, 'first_name', '') or ''
        sender_username = getattr(sender, 'username', None)
        user_tag = f"@{sender_username}" if sender_username else f"`{event.sender_id}`"
        channel_msg = (
            f"📨 **Consulta via Inline**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} ({user_tag})\n"
            f"🆔 **ID:** `{event.sender_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n{result}"
        )
        await bot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal (inline): {e}")

# ══════════════════════════════════════════════
#  BOT — AUTOMS PRO (com botões inline)
# ══════════════════════════════════════════════

AUTOMS_PER_PAGE = 5

def build_automs_page(page=0):
    automs = load_automs()
    total = len(automs)
    total_pages = max(1, math.ceil(total / AUTOMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * AUTOMS_PER_PAGE
    end = start + AUTOMS_PER_PAGE
    page_automs = automs[start:end]

    text = (
        f"╔══════════════════════════════╗\n"
        f"║   💬 AUTOMS - RESPOSTAS AUTO  ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Total:** `{total}` mensagem(ns)\n"
        f"📄 **Página:** `{page + 1}/{total_pages}`\n\n"
    )

    if not page_automs:
        text += "📭 Nenhuma mensagem automática cadastrada.\n"
    else:
        for i, am in enumerate(page_automs, start=start + 1):
            status = "✅" if am.get("ativa", True) else "❌"
            preview = am['message'][:50] + "..." if len(am['message']) > 50 else am['message']
            title_str = am.get('title') or '(sem título)'
            text += f"**{i}.** {status} 📌 **{title_str}**\n   _{preview}_\n\n"

    text += "╚══════════════════════════════╝"

    buttons = []
    for idx, am in enumerate(page_automs):
        real_idx = start + idx
        status_icon = "✅" if am.get("ativa", True) else "❌"
        buttons.append([
            Button.inline(f"👁 Ver", data=f"viewautom:{real_idx}"),
            Button.inline(f"✏️ Editar", data=f"editautom:{real_idx}"),
            Button.inline(f"{status_icon} On/Off", data=f"toggleautom:{real_idx}"),
            Button.inline(f"🗑", data=f"rmautom:{real_idx}")
        ])

    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("◀️ Voltar", data=f"autompage:{page - 1}"))
    if total > 0:
        nav_row.append(Button.inline(f"📄 {page + 1}/{total_pages}", data="noop"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Avançar ▶️", data=f"autompage:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        Button.inline("➕ Adicionar", data="addautom_prompt"),
        Button.inline("🔄 Atualizar", data="autompage:0"),
        Button.inline("⛔ Fechar", data="close_panel")
    ])

    return text, buttons

@bot.on(events.NewMessage(pattern=r'^/automs$'))
async def bot_automs(event):
    if event.sender_id != OWNER_ID:
        return
    text, buttons = build_automs_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^autompage:(\d+)$'))
async def bot_callback_autom_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_automs_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^viewautom:(\d+)$'))
async def bot_callback_view_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    automs = load_automs()
    if 0 <= idx < len(automs):
        am = automs[idx]
        status = "✅ Ativa" if am.get("ativa", True) else "❌ Inativa"
        title_str = am.get('title') or '(sem título)'
        await event.answer()
        await event.reply(
            f"╔══════════════════════════════╗\n"
            f"║   📌 AUTOM #{idx + 1}                ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n"
            f"📋 **Título:** {title_str}\n"
            f"📊 **Status:** {status}\n"
            f"📅 **Criada:** {am.get('criada_em', 'N/D')}\n\n"
            f"💬 **Mensagem:**\n{am['message']}\n"
            f"\n╚══════════════════════════════╝",
            buttons=[
                [
                    Button.inline("✏️ Editar", data=f"editautom:{idx}"),
                    Button.inline("🔄 On/Off", data=f"toggleautom:{idx}"),
                    Button.inline("🗑 Apagar", data=f"rmautom:{idx}")
                ],
                [Button.inline("📤 Enviar", data=f"sendautom:{idx}"),
                 Button.inline("◀️ Voltar", data="autompage:0")]
            ],
            parse_mode='md'
        )
    else:
        await event.answer("❌ Mensagem não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^toggleautom:(\d+)$'))
async def bot_callback_toggle_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    toggled = toggle_autom(idx)
    if toggled:
        status = "✅ Ativada" if toggled.get("ativa") else "❌ Desativada"
        await event.answer(f"{status}: {toggled.get('title', 'msg')}", alert=True)
    else:
        await event.answer("❌ Não encontrada.", alert=True)
    text, buttons = build_automs_page(0)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^editautom:(\d+)$'))
async def bot_callback_edit_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    automs = load_automs()
    if 0 <= idx < len(automs):
        edit_states[event.sender_id] = {"action": "edit_autom", "index": idx, "step": "choose"}
        await event.answer()
        await event.reply(
            f"✏️ **Editando AutoM #{idx + 1}**\n\nO que deseja editar?",
            buttons=[
                [Button.inline("📋 Título", data=f"editfield:title:{idx}"),
                 Button.inline("💬 Mensagem", data=f"editfield:message:{idx}")],
                [Button.inline("❌ Cancelar", data="canceledit")]
            ],
            parse_mode='md'
        )
    else:
        await event.answer("❌ Não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^editfield:(title|message):(\d+)$'))
async def bot_callback_edit_field(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    field = event.pattern_match.group(1)
    idx = int(event.pattern_match.group(2))
    edit_states[event.sender_id] = {"action": "edit_autom", "index": idx, "step": "waiting", "field": field}
    await event.answer()
    field_name = "título" if field == "title" else "mensagem"
    await event.reply(
        f"✏️ Envie o novo **{field_name}** para a AutoM #{idx + 1}:\n\n(Envie qualquer texto ou /cancelar)",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^canceledit$'))
async def bot_callback_cancel_edit(event):
    edit_states.pop(event.sender_id, None)
    await event.answer("❌ Edição cancelada.")
    await event.delete()

@bot.on(events.CallbackQuery(pattern=r'^sendautom:(\d+)$'))
async def bot_callback_send_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    automs = load_automs()
    if 0 <= idx < len(automs):
        edit_states[event.sender_id] = {"action": "send_autom", "index": idx, "step": "waiting_target"}
        await event.answer()
        await event.reply(
            f"📤 **Enviar AutoM #{idx + 1}**\n\n"
            f"Envie o **ID do chat** ou **@username** do destinatário:\n\n"
            f"💡 Pode enviar para usuário ou grupo.\nEnvie /cancelar para desistir.",
            parse_mode='md'
        )
    else:
        await event.answer("❌ Não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^close_panel$'))
async def bot_callback_close(event):
    await event.answer("✅ Painel fechado.")
    await event.delete()

@bot.on(events.CallbackQuery(pattern=r'^rmautom:(\d+)$'))
async def bot_callback_remove_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    removed = remove_autom(idx)
    if removed:
        await event.answer(f"✅ AutoM '{removed.get('title', 'msg')}' removida!", alert=True)
    else:
        await event.answer("❌ Não encontrada.", alert=True)
    text, buttons = build_automs_page(0)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^addautom_prompt$'))
async def bot_callback_add_autom_prompt(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    await event.answer()
    await event.reply(
        "╔══════════════════════════════╗\n"
        "║   ➕ ADICIONAR AUTOM          ║\n"
        "╚══════════════════════════════╝\n"
        "\n"
        "Envie no formato:\n"
        "`/addautom Título | Mensagem`\n\n"
        "💡 Título é **opcional**:\n"
        "`/addautom | Apenas a mensagem`\n"
        "\n╚══════════════════════════════╝",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'^/addautom\s+(.+)$'))
async def bot_add_autom(event):
    if event.sender_id != OWNER_ID:
        return
    text = event.pattern_match.group(1).strip()
    if '|' in text:
        parts = text.split('|', 1)
        title = parts[0].strip()
        message = parts[1].strip()
    else:
        title = ""
        message = text

    if not message:
        await event.reply("❌ A mensagem não pode estar vazia.", parse_mode='md')
        return

    count = add_autom(title, message)
    title_str = title or "(sem título)"
    await event.reply(
        f"✅ **AutoM adicionada!**\n\n"
        f"📌 **Título:** {title_str}\n"
        f"💬 **Preview:** {message[:80]}{'...' if len(message) > 80 else ''}\n"
        f"📊 **Total:** `{count}` mensagem(ns)\n\nUse /automs para gerenciar.",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  BOT — MENSAGENS PRONTAS PRO
# ══════════════════════════════════════════════

MSGS_PER_PAGE = 5

def build_msgs_prontas_page(page=0):
    msgs = load_msgs_prontas()
    total = len(msgs)
    total_pages = max(1, math.ceil(total / MSGS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * MSGS_PER_PAGE
    end = start + MSGS_PER_PAGE
    page_msgs = msgs[start:end]

    text = (
        f"╔══════════════════════════════╗\n"
        f"║   📝 MENSAGENS PRONTAS        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Total:** `{total}` mensagem(ns)\n"
        f"📄 **Página:** `{page + 1}/{total_pages}`\n\n"
    )

    if not page_msgs:
        text += "📭 Nenhuma mensagem pronta cadastrada.\n"
    else:
        for i, mp in enumerate(page_msgs, start=start + 1):
            status = "✅" if mp.get("ativa", True) else "❌"
            preview = mp['message'][:50] + "..." if len(mp['message']) > 50 else mp['message']
            title_str = mp.get('title') or '(sem título)'
            text += f"**{i}.** {status} 📌 **{title_str}**\n   _{preview}_\n\n"

    text += "╚══════════════════════════════╝"

    buttons = []
    for idx, mp in enumerate(page_msgs):
        real_idx = start + idx
        buttons.append([
            Button.inline(f"👁 Ver", data=f"viewmp:{real_idx}"),
            Button.inline(f"✏️ Edit", data=f"editmp:{real_idx}"),
            Button.inline(f"📤 Enviar", data=f"sendmp:{real_idx}"),
            Button.inline(f"🗑", data=f"rmmp:{real_idx}")
        ])

    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("◀️ Voltar", data=f"mppage:{page - 1}"))
    if total > 0:
        nav_row.append(Button.inline(f"📄 {page + 1}/{total_pages}", data="noop"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Avançar ▶️", data=f"mppage:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        Button.inline("➕ Adicionar", data="addmp_prompt"),
        Button.inline("🔄 Atualizar", data="mppage:0"),
        Button.inline("⛔ Fechar", data="close_panel")
    ])

    return text, buttons

@bot.on(events.NewMessage(pattern=r'^/msgprontas$'))
async def bot_msgs_prontas(event):
    if event.sender_id != OWNER_ID:
        return
    text, buttons = build_msgs_prontas_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^mppage:(\d+)$'))
async def bot_callback_mp_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_msgs_prontas_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^viewmp:(\d+)$'))
async def bot_callback_view_mp(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    msgs = load_msgs_prontas()
    if 0 <= idx < len(msgs):
        mp = msgs[idx]
        status = "✅ Ativa" if mp.get("ativa", True) else "❌ Inativa"
        title_str = mp.get('title') or '(sem título)'
        await event.answer()
        await event.reply(
            f"╔══════════════════════════════╗\n"
            f"║   📝 MSG PRONTA #{idx + 1}           ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n"
            f"📋 **Título:** {title_str}\n"
            f"📊 **Status:** {status}\n"
            f"📅 **Criada:** {mp.get('criada_em', 'N/D')}\n\n"
            f"💬 **Mensagem:**\n{mp['message']}\n"
            f"\n╚══════════════════════════════╝",
            buttons=[
                [Button.inline("✏️ Editar", data=f"editmp:{idx}"),
                 Button.inline("📤 Enviar", data=f"sendmp:{idx}"),
                 Button.inline("🗑 Apagar", data=f"rmmp:{idx}")],
                [Button.inline("◀️ Voltar", data="mppage:0")]
            ],
            parse_mode='md'
        )
    else:
        await event.answer("❌ Não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^editmp:(\d+)$'))
async def bot_callback_edit_mp(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    msgs = load_msgs_prontas()
    if 0 <= idx < len(msgs):
        await event.answer()
        await event.reply(
            f"✏️ **Editando Msg Pronta #{idx + 1}**\n\nO que deseja editar?",
            buttons=[
                [Button.inline("📋 Título", data=f"editmpfield:title:{idx}"),
                 Button.inline("💬 Mensagem", data=f"editmpfield:message:{idx}")],
                [Button.inline("❌ Cancelar", data="canceledit")]
            ],
            parse_mode='md'
        )
    else:
        await event.answer("❌ Não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^editmpfield:(title|message):(\d+)$'))
async def bot_callback_edit_mp_field(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    field = event.pattern_match.group(1)
    idx = int(event.pattern_match.group(2))
    edit_states[event.sender_id] = {"action": "edit_msgpronta", "index": idx, "step": "waiting", "field": field}
    await event.answer()
    field_name = "título" if field == "title" else "mensagem"
    await event.reply(
        f"✏️ Envie o novo **{field_name}** para a Msg Pronta #{idx + 1}:\n\n(Envie qualquer texto ou /cancelar)",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^sendmp:(\d+)$'))
async def bot_callback_send_mp(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    msgs = load_msgs_prontas()
    if 0 <= idx < len(msgs):
        edit_states[event.sender_id] = {"action": "send_msgpronta", "index": idx, "step": "waiting_target"}
        await event.answer()
        await event.reply(
            f"📤 **Enviar Msg Pronta #{idx + 1}**\n\n"
            f"Envie o **ID do chat** ou **@username** do destinatário:\n\nEnvie /cancelar para desistir.",
            parse_mode='md'
        )
    else:
        await event.answer("❌ Não encontrada.", alert=True)

@bot.on(events.CallbackQuery(pattern=r'^rmmp:(\d+)$'))
async def bot_callback_remove_mp(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    removed = remove_msg_pronta(idx)
    if removed:
        await event.answer(f"✅ Msg '{removed.get('title', 'msg')}' removida!", alert=True)
    else:
        await event.answer("❌ Não encontrada.", alert=True)
    text, buttons = build_msgs_prontas_page(0)
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^addmp_prompt$'))
async def bot_callback_add_mp_prompt(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    await event.answer()
    await event.reply(
        "╔══════════════════════════════╗\n"
        "║   ➕ ADICIONAR MSG PRONTA     ║\n"
        "╚══════════════════════════════╝\n"
        "\n**Opção 1** - Comando rápido:\n`/addmsg Título | Mensagem`\n\n"
        "**Opção 2** - Passo a passo:\nClique abaixo para iniciar.",
        buttons=[
            [Button.inline("📝 Criar passo a passo", data="addmp_wizard")],
            [Button.inline("❌ Cancelar", data="close_panel")]
        ],
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^addmp_wizard$'))
async def bot_callback_add_mp_wizard(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    edit_states[event.sender_id] = {"action": "add_msgpronta", "step": "title", "title": "", "message": ""}
    await event.answer()
    await event.reply(
        "📋 **Passo 1/2 — Título**\n\nEnvie o **título** da mensagem pronta:\n(Pode enviar vazio para pular)\n\nEnvie /cancelar para desistir.",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'^/addmsg\s+(.+)$'))
async def bot_add_msg_pronta(event):
    if event.sender_id != OWNER_ID:
        return
    text = event.pattern_match.group(1).strip()
    if '|' in text:
        parts = text.split('|', 1)
        title = parts[0].strip()
        message = parts[1].strip()
    else:
        title = ""
        message = text

    if not message:
        await event.reply("❌ A mensagem não pode estar vazia.", parse_mode='md')
        return

    count = add_msg_pronta(title, message)
    title_str = title or "(sem título)"
    await event.reply(
        f"✅ **Mensagem pronta adicionada!**\n\n"
        f"📌 **Título:** {title_str}\n"
        f"💬 **Preview:** {message[:80]}{'...' if len(message) > 80 else ''}\n"
        f"📊 **Total:** `{count}`\n\nUse /msgprontas para gerenciar.",
        buttons=[
            [Button.inline("👁 Review", data=f"viewmp:{count - 1}"),
             Button.inline("📝 Lista", data="mppage:0")]
        ],
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  BOT — AUTO-REPLY PANEL
# ══════════════════════════════════════════════

def build_autoreply_panel():
    ar = load_autoreply()
    status = "✅ ATIVO" if ar.get("ativo") else "❌ INATIVO"
    msg_preview = ar.get("mensagem", "")[:100] or "(nenhuma mensagem configurada)"

    text = (
        f"╔══════════════════════════════╗\n"
        f"║   🔄 AUTO-REPLY EM DMs        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Status:** {status}\n"
        f"💬 **Mensagem:**\n_{msg_preview}_\n"
        f"\nQuando ativo, responde automaticamente\na qualquer pessoa que iniciar DM.\n"
        f"\n╚══════════════════════════════╝"
    )

    is_active = ar.get("ativo", False)
    buttons = [
        [Button.inline("✅ Ativar" if not is_active else "❌ Desativar", data="ar_toggle"),
         Button.inline("✏️ Editar Mensagem", data="ar_edit")],
        [Button.inline("👁 Ver Completa", data="ar_view"),
         Button.inline("⛔ Fechar", data="close_panel")]
    ]
    return text, buttons

@bot.on(events.NewMessage(pattern=r'^/autoreply$'))
async def bot_autoreply(event):
    if event.sender_id != OWNER_ID:
        return
    text, buttons = build_autoreply_panel()
    await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^ar_panel$'))
async def bot_callback_ar_panel(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    text, buttons = build_autoreply_panel()
    try:
        await event.edit(text, buttons=buttons, parse_mode='md')
    except Exception:
        await event.answer()
        await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^ar_toggle$'))
async def bot_callback_ar_toggle(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    ar = load_autoreply()
    new_state = not ar.get("ativo", False)
    set_autoreply(new_state)
    status = "✅ Ativado" if new_state else "❌ Desativado"
    await event.answer(f"Auto-Reply {status}!", alert=True)
    text, buttons = build_autoreply_panel()
    await event.edit(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^ar_edit$'))
async def bot_callback_ar_edit(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    edit_states[event.sender_id] = {"action": "set_autoreply", "step": "waiting"}
    await event.answer()
    await event.reply(
        "✏️ **Envie a nova mensagem de auto-reply:**\n\nSuporta **Markdown**.\nEnvie /cancelar para desistir.",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=r'^ar_view$'))
async def bot_callback_ar_view(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    ar = load_autoreply()
    msg = ar.get("mensagem", "(vazia)")
    await event.answer()
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   💬 MENSAGEM AUTO-REPLY      ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n{msg}\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  BOT — GESTÃO DE USUÁRIOS
# ══════════════════════════════════════════════

USERS_PER_PAGE = 8

def build_users_page(page=0):
    users = load_users()
    total = len(users)
    total_pages = max(1, math.ceil(total / USERS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    page_users = users[start:end]

    text = (
        f"╔══════════════════════════════╗\n"
        f"║   👥 USUÁRIOS REGISTRADOS     ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"📊 **Total:** `{total}` usuário(s)\n"
        f"📄 **Página:** `{page + 1}/{total_pages}`\n\n"
    )

    if not page_users:
        text += "📭 Nenhum usuário registrado.\n"
    else:
        for i, u in enumerate(page_users, start=start + 1):
            uname = f"@{u['username']}" if u.get('username') else "N/A"
            text += f"**{i}.** `{u['id']}` — {u['nome']} ({uname})\n"

    text += f"\n╚══════════════════════════════╝"

    buttons = []
    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("◀️ Voltar", data=f"userspage:{page - 1}"))
    nav_row.append(Button.inline(f"📄 {page + 1}/{total_pages}", data="noop"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Avançar ▶️", data=f"userspage:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        Button.inline("🔄 Atualizar", data="userspage:0"),
        Button.inline("⛔ Fechar", data="close_panel")
    ])

    return text, buttons

@bot.on(events.NewMessage(pattern=r'^/usuarios$'))
async def bot_usuarios(event):
    if event.sender_id != OWNER_ID:
        return
    text, buttons = build_users_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')

@bot.on(events.CallbackQuery(pattern=r'^userspage:(\d+)$'))
async def bot_callback_users_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_users_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')

# ══════════════════════════════════════════════
#  BOT — /broadcast
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'^/broadcast\s+(.+)$'))
async def bot_broadcast(event):
    if event.sender_id != OWNER_ID:
        return
    msg = event.pattern_match.group(1).strip()
    users = load_users()
    sent = 0
    failed = 0

    status_msg = await event.reply(
        f"📣 **Broadcast em andamento...**\n\n"
        f"📊 Total: `{len(users)}` usuário(s)\n⏳ Enviando...",
        parse_mode='md'
    )

    for u in users:
        try:
            await bot.send_message(u["id"], msg, parse_mode='md')
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit(
        f"╔══════════════════════════════╗\n"
        f"║   📣 BROADCAST CONCLUÍDO      ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Enviados:** `{sent}`\n"
        f"❌ **Falharam:** `{failed}`\n"
        f"📊 **Total:** `{len(users)}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  HANDLE EDIT STATE (automs, msgs prontas, auto-reply)
# ══════════════════════════════════════════════

async def handle_edit_state(event, state):
    """Processa estados de edição/envio em andamento."""
    if event.raw_text == "/cancelar":
        edit_states.pop(event.sender_id, None)
        await event.reply("❌ Operação cancelada.")
        return

    # --- Edit AutoM ---
    if state["action"] == "edit_autom" and state["step"] == "waiting":
        idx = state["index"]
        field = state["field"]
        new_value = event.raw_text.strip()

        if field == "title":
            updated = update_autom(idx, title=new_value)
        else:
            updated = update_autom(idx, message=new_value)

        edit_states.pop(event.sender_id, None)

        if updated:
            field_name = "Título" if field == "title" else "Mensagem"
            await event.reply(
                f"✅ **{field_name} atualizado!**\n\n"
                f"📌 **Título:** {updated.get('title') or '(sem título)'}\n"
                f"💬 **Preview:** {updated['message'][:80]}...\n\nUse /automs para gerenciar.",
                parse_mode='md'
            )
        else:
            await event.reply("❌ Erro ao atualizar.", parse_mode='md')

    # --- Set Auto-Reply ---
    elif state["action"] == "set_autoreply":
        new_msg = event.raw_text.strip()
        set_autoreply(True, new_msg)
        edit_states.pop(event.sender_id, None)
        await event.reply(
            f"✅ **Auto-Reply configurado e ativado!**\n\n💬 **Mensagem:**\n{new_msg}\n\nUse /autoreply para gerenciar.",
            parse_mode='md'
        )

    # --- Edit Msg Pronta ---
    elif state["action"] == "edit_msgpronta" and state["step"] == "waiting":
        idx = state["index"]
        field = state["field"]
        new_value = event.raw_text.strip()

        if field == "title":
            updated = update_msg_pronta(idx, title=new_value)
        else:
            updated = update_msg_pronta(idx, message=new_value)

        edit_states.pop(event.sender_id, None)

        if updated:
            field_name = "Título" if field == "title" else "Mensagem"
            await event.reply(
                f"✅ **{field_name} atualizado!**\n\n"
                f"📌 **Título:** {updated.get('title') or '(sem título)'}\n"
                f"💬 **Preview:** {updated['message'][:80]}...\n\nUse /msgprontas para gerenciar.",
                parse_mode='md'
            )
        else:
            await event.reply("❌ Erro ao atualizar.", parse_mode='md')

    # --- Add Msg Pronta step by step ---
    elif state["action"] == "add_msgpronta":
        if state["step"] == "title":
            title = event.raw_text.strip()
            edit_states[event.sender_id] = {"action": "add_msgpronta", "step": "message", "title": title}
            await event.reply(
                f"📋 Título: **{title or '(vazio)'}**\n\nAgora envie a **mensagem** (suporta Markdown):\n\nEnvie /cancelar para desistir.",
                parse_mode='md'
            )
        elif state["step"] == "message":
            message = event.raw_text.strip()
            title = state.get("title", "")
            if not message:
                await event.reply("❌ A mensagem não pode estar vazia.")
                return
            count = add_msg_pronta(title, message)
            edit_states.pop(event.sender_id, None)
            await event.reply(
                f"✅ **Mensagem pronta adicionada!**\n\n"
                f"📌 **Título:** {title or '(sem título)'}\n"
                f"💬 **Preview:** {message[:80]}{'...' if len(message) > 80 else ''}\n"
                f"📊 **Total:** `{count}`\n\nUse /msgprontas para gerenciar.",
                buttons=[
                    [Button.inline("👁 Review", data=f"viewmp:{count - 1}"),
                     Button.inline("📝 Lista", data="mppage:0")]
                ],
                parse_mode='md'
            )

    # --- Send AutoM to target ---
    elif state["action"] == "send_autom" and state["step"] == "waiting_target":
        target = event.raw_text.strip()
        idx = state["index"]
        automs = load_automs()
        edit_states.pop(event.sender_id, None)

        if 0 <= idx < len(automs):
            am = automs[idx]
            try:
                if target.startswith("@"):
                    entity = await bot.get_entity(target)
                elif target.lstrip("-").isdigit():
                    entity = await bot.get_entity(int(target))
                else:
                    entity = await bot.get_entity(target)

                msg_text = ""
                if am.get("title"):
                    msg_text += f"📌 **{am['title']}**\n\n"
                msg_text += am["message"]

                await bot.send_message(entity, msg_text, parse_mode='md')
                target_name = getattr(entity, 'title', None) or getattr(entity, 'first_name', str(target))
                await event.reply(
                    f"✅ **Mensagem enviada!**\n\n📌 **AutoM:** {am.get('title') or '(sem título)'}\n📤 **Para:** {target_name}",
                    parse_mode='md'
                )
            except Exception as e:
                await event.reply(f"❌ Erro ao enviar: `{str(e)[:100]}`", parse_mode='md')
        else:
            await event.reply("❌ AutoM não encontrada.", parse_mode='md')

    # --- Send Msg Pronta to target ---
    elif state["action"] == "send_msgpronta" and state["step"] == "waiting_target":
        target = event.raw_text.strip()
        idx = state["index"]
        msgs = load_msgs_prontas()
        edit_states.pop(event.sender_id, None)

        if 0 <= idx < len(msgs):
            mp = msgs[idx]
            try:
                if target.startswith("@"):
                    entity = await bot.get_entity(target)
                elif target.lstrip("-").isdigit():
                    entity = await bot.get_entity(int(target))
                else:
                    entity = await bot.get_entity(target)

                msg_text = ""
                if mp.get("title"):
                    msg_text += f"📌 **{mp['title']}**\n\n"
                msg_text += mp["message"]

                await bot.send_message(entity, msg_text, parse_mode='md')
                target_name = getattr(entity, 'title', None) or getattr(entity, 'first_name', str(target))
                await event.reply(
                    f"✅ **Mensagem pronta enviada!**\n\n📌 **Msg:** {mp.get('title') or '(sem título)'}\n📤 **Para:** {target_name}",
                    parse_mode='md'
                )
            except Exception as e:
                await event.reply(f"❌ Erro ao enviar: `{str(e)[:100]}`", parse_mode='md')
        else:
            await event.reply("❌ Mensagem pronta não encontrada.", parse_mode='md')

# ══════════════════════════════════════════════
#  BOT — CALLBACKS DO PAINEL IPTV
# ══════════════════════════════════════════════

@bot.on(events.CallbackQuery)
async def on_panel_cb(event):
    uid = event.sender_id
    d = event.data.decode()

    # Apenas callbacks do painel (prefixo panel_)
    if not d.startswith("panel_"):
        return

    d = d[6:]  # Remove "panel_"

    if d == "menu":
        s = sm.get_session(uid)
        if not s:
            await event.answer("Sessao expirada. /painel", alert=True)
            return
        sm.clear_state(uid)
        dash = PainelAPI.dashboard(s)
        if not dash:
            sm.logout(uid)
            await event.answer("Sessao expirada", alert=True)
            return
        cr = PainelAPI.credits(s)
        await event.edit(PainelUI.dash_text(sm.get_username(uid), cr, dash), buttons=PainelUI.main_menu(), parse_mode="md")
        return

    if d == "logout":
        sm.logout(uid)
        await event.edit(f"{E['exit']} **Desconectado**\n\nUse /painel\n\n{E['crown']} {OWNER_USERNAME}", parse_mode="md")
        return

    s = sm.get_session(uid)
    if not s:
        await event.answer("Sessao expirada. /painel", alert=True)
        return

    # DASHBOARD
    if d == "dash":
        await event.answer(E["load"])
        dash = PainelAPI.dashboard(s)
        cr = PainelAPI.credits(s)
        stats = PainelAPI.stats(s)
        sl = PainelAPI.sales(s)
        un = sm.get_username(uid)
        iptv = dash.get("iptv", {}) if dash else {}
        p2p = dash.get("p2p", {}) if dash else {}
        t = (
            f"{E['dash']} **DASHBOARD**\n{LINE}\n\n"
            f"{E['user']} `{un}` | {E['credit']} `{cr.get('credits', 'N/A') if cr else 'N/A'}`\n\n"
            f"{E['tv']} **IPTV** - Ativos: `{iptv.get('active_clients_count', 0)}` | Online: `{iptv.get('online_clients_count', 0)}`\n"
            f"{E['p2p']} **P2P** - Ativos: `{p2p.get('active_clients_count', 0)}` | Online: `{p2p.get('online_clients_count', 0)}`\n"
        )
        if stats and isinstance(stats, dict):
            t += f"\n{THIN}\n{E['dash']} **Estatisticas**\n"
            for k, v in stats.items():
                if isinstance(v, (str, int, float)):
                    t += f"   {str(k).replace('_',' ').title()}: `{v}`\n"
        if sl and isinstance(sl, dict):
            t += f"\n{E['credit']} **Vendas**\n"
            for k, v in sl.items():
                if isinstance(v, (str, int, float)):
                    t += f"   {str(k).replace('_',' ').title()}: `{v}`\n"
        t += f"\n{LINE}"
        await event.edit(t, buttons=[
            [Button.inline(f"{E['refresh']} Atualizar", b"panel_dash")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # LISTAS
    if d == "iptv_list":
        await event.answer(E["load"])
        cl = sm.get_cache(uid, "iptv") or PainelAPI.iptv_clients(s)
        sm.set_cache(uid, "iptv", cl)
        sm.set_page_data(uid, cl, "iptv")
        t, b = PainelUI.client_list(cl, 0, E["tv"], "Clientes IPTV", "iptv")
        await event.edit(t, buttons=b, parse_mode="md")
        return

    if d == "p2p_list":
        await event.answer(E["load"])
        cl = sm.get_cache(uid, "p2p") or PainelAPI.p2p_clients(s)
        sm.set_cache(uid, "p2p", cl)
        sm.set_page_data(uid, cl, "p2p")
        t, b = PainelUI.client_list(cl, 0, E["p2p"], "Clientes P2P", "p2p")
        await event.edit(t, buttons=b, parse_mode="md")
        return

    # PAGINACAO
    if "_pg_" in d:
        parts = d.rsplit("_pg_", 1)
        try:
            page = int(parts[1])
        except ValueError:
            return
        pd = sm.get_page_data(uid)
        if not pd:
            await event.answer("Expirado", alert=True)
            return
        em = {"iptv": E["tv"], "p2p": E["p2p"], "search": E["search"], "resellers": E["rev"]}
        nm = {"iptv": "Clientes IPTV", "p2p": "Clientes P2P", "search": "Resultados", "resellers": "Revendedores"}
        pt = pd["type"]
        t, b = PainelUI.client_list(pd["items"], page, em.get(pt, E["info"]), nm.get(pt, "Lista"), pt)
        await event.edit(t, buttons=b, parse_mode="md")
        return

    # DETALHE
    if d.startswith("det_"):
        parts = d.split("_", 2)
        if len(parts) < 3:
            return
        cpfx, cid = parts[1], parts[2]
        pd = sm.get_page_data(uid)
        if not pd:
            await event.answer("Expirado", alert=True)
            return
        c = next((x for x in pd["items"] if str(x.get("id", "")) == cid), None)
        if not c:
            await event.answer("Nao encontrado", alert=True)
            return
        st = f"{E['online']} Online" if c.get("online") else f"{E['offline']} Offline"
        t = (
            f"{E['info']} **Detalhes**\n{LINE}\n\n"
            f"{E['user']} `{c.get('username', 'N/A')}`\n"
            f"Status: {st}\n"
            f"{E['time']} Exp: `{c.get('exp_date', 'N/A')}`\n"
            f"Criado: `{c.get('created_at', 'N/A')}`\n"
            f"Max conn: `{c.get('max_connections', 'N/A')}`\n"
            f"ID: `{cid}`\n\n{LINE}"
        )
        tk = "iptv" if "iptv" in cpfx else "p2p"
        await event.edit(t, buttons=[
            [Button.inline(f"{E['edit']} Senha", f"panel_epw_{tk}_{cid}".encode()),
             Button.inline(f"{E['fast']} Fast Msg", f"panel_fm_{cid}".encode())],
            [Button.inline(f"{E['del']} Remover", f"panel_dc_{tk}_{cid}".encode())],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # EDITAR SENHA
    if d.startswith("epw_"):
        _, ct, cid = d.split("_", 2)
        sm.set_state(uid, "panel_edit_pw", {"type": ct, "id": cid})
        await event.edit(f"{E['edit']} **Nova senha** para ID `{cid}`:", buttons=PainelUI.cancel(), parse_mode="md")
        return

    # FAST MSG DIRETO
    if d.startswith("fm_"):
        cid = d[3:]
        ok = PainelAPI.fast_message(s, cid)
        await event.answer(f"{E['ok']} Enviada!" if ok else f"{E['err']} Falha", alert=True)
        return

    # REMOVER
    if d.startswith("dc_"):
        _, ct, cid = d.split("_", 2)
        await event.edit(
            f"{E['del']} **Remover ID `{cid}`?**\n\n{E['warn']} Irreversivel!",
            buttons=PainelUI.confirm(f"panel_xd_{ct}_{cid}".encode()), parse_mode="md"
        )
        return

    if d.startswith("xd_"):
        _, ct, cid = d.split("_", 2)
        ok = PainelAPI.delete_client(s, ct, cid)
        sm.clear_cache(uid)
        await event.edit(f"{E['ok'] if ok else E['err']} {'Removido!' if ok else 'Falha.'}\n\nID: `{cid}`",
                         buttons=PainelUI.back(), parse_mode="md")
        return

    # REVENDEDORES
    if d == "resellers":
        await event.answer(E["load"])
        rl = PainelAPI.resellers(s)
        if not rl:
            await event.edit(f"{E['rev']} **Revendedores**\n\n{E['warn']} Vazio.", buttons=PainelUI.back(), parse_mode="md")
            return
        sm.set_page_data(uid, rl, "resellers")
        t, b = PainelUI.client_list(rl, 0, E["rev"], "Revendedores", "resellers")
        await event.edit(t, buttons=b, parse_mode="md")
        return

    # CONEXOES
    if d == "connections":
        await event.answer(E["load"])
        cn = PainelAPI.connections(s)
        if not cn:
            await event.edit(f"{E['conn']} **Conexoes**\n\n{E['warn']} Nenhuma ativa.", buttons=[
                [Button.inline(f"{E['refresh']} Atualizar", b"panel_connections")],
                [Button.inline(f"{E['back']} Menu", b"panel_menu")],
            ], parse_mode="md")
            return
        lines = [f"{E['conn']} **CONEXOES** - `{len(cn)}`\n{LINE}\n"]
        for i, c in enumerate(cn[:20]):
            lines.append(
                f"`{i+1}.` {E['online']} `{c.get('username', '?')}`\n"
                f"     {E['ip']} `{c.get('ip', '?')}` | {E['device']} `{c.get('device', '?')}` | {E['time']} `{c.get('duration', '?')}`"
            )
        if len(cn) > 20:
            lines.append(f"\n{E['warn']} +{len(cn)-20} conexoes")
        lines.append(f"\n{LINE}")
        await event.edit("\n".join(lines), buttons=[
            [Button.inline(f"{E['refresh']} Atualizar", b"panel_connections")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # BUSCAR
    if d == "search":
        sm.set_state(uid, "panel_search_term")
        await event.edit(f"{E['search']} **Buscar**\n\nDigite o **username:**", buttons=PainelUI.cancel(), parse_mode="md")
        return

    # FAST MSG
    if d == "fast_msg":
        sm.set_state(uid, "panel_fast_msg_id")
        await event.edit(f"{E['fast']} **Fast Message**\n\nDigite o **ID:**", buttons=PainelUI.cancel(), parse_mode="md")
        return

    # CRIAR IPTV
    if d == "create_iptv":
        sm.set_state(uid, "panel_ci_user", {})
        await event.edit(f"{E['create']} **Criar IPTV**\n{LINE}\n\n{E['user']} **Username:**", buttons=PainelUI.cancel(), parse_mode="md")
        return

    if d == "ok_iptv":
        st = sm.get_state(uid)
        if not st or st["step"] != "panel_ci_confirm":
            return
        dd = st["data"]
        sm.clear_state(uid)
        await event.edit(f"{E['load']} Criando IPTV...", parse_mode="md")
        ok, info = PainelAPI.create_iptv(s, dd["username"], dd["password"], dd["bouquet"], dd["expiry"])
        sm.clear_cache(uid)
        if ok:
            text = format_panel_result(info, "Cliente IPTV Criado", E["ok"])
        else:
            err = info.get("error", info.get("message", "Erro desconhecido"))
            text = f"{E['err']} **Falha IPTV**\n\n`{dd['username']}` - `{err}`"
        await event.edit(text, buttons=[
            [Button.inline(f"{E['create']} Criar Outro", b"panel_create_iptv")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # CRIAR P2P
    if d == "create_p2p":
        sm.set_state(uid, "panel_cp_user", {})
        await event.edit(f"{E['create']} **Criar P2P**\n{LINE}\n\n{E['user']} **Username:**", buttons=PainelUI.cancel(), parse_mode="md")
        return

    if d == "ok_p2p":
        st = sm.get_state(uid)
        if not st or st["step"] != "panel_cp_confirm":
            return
        dd = st["data"]
        sm.clear_state(uid)
        await event.edit(f"{E['load']} Criando P2P...", parse_mode="md")
        ok, info = PainelAPI.create_p2p(s, dd["username"], dd["password"], dd["expiry"])
        sm.clear_cache(uid)
        if ok:
            text = format_panel_result(info, "Cliente P2P Criado", E["ok"])
        else:
            err = info.get("error", info.get("message", "Erro desconhecido"))
            text = f"{E['err']} **Falha P2P**\n\n`{dd['username']}` - `{err}`"
        await event.edit(text, buttons=[
            [Button.inline(f"{E['create']} Criar Outro", b"panel_create_p2p")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # CRIAR REVENDEDOR
    if d == "create_rev":
        sm.set_state(uid, "panel_cr_user", {})
        await event.edit(f"{E['create']} **Criar Revendedor**\n{LINE}\n\n{E['user']} **Username:**", buttons=PainelUI.cancel(), parse_mode="md")
        return

    if d == "ok_rev":
        st = sm.get_state(uid)
        if not st or st["step"] != "panel_cr_confirm":
            return
        dd = st["data"]
        sm.clear_state(uid)
        await event.edit(f"{E['load']} Criando revendedor...", parse_mode="md")
        ok, info = PainelAPI.create_reseller(s, dd["username"], dd["password"], dd["credits"])
        sm.clear_cache(uid)
        if ok:
            text = format_panel_result(info, "Revendedor Criado", E["ok"])
        else:
            err = info.get("error", info.get("message", "Erro desconhecido"))
            text = f"{E['err']} **Falha**\n\n`{dd['username']}` - `{err}`"
        await event.edit(text, buttons=[
            [Button.inline(f"{E['create']} Criar Outro", b"panel_create_rev")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # TESTES
    if d == "tests":
        await event.edit(f"{E['test']} **Teste Rapido**\n{LINE}\n\nSelecione:", buttons=[
            [Button.inline(f"{E['tv']} IPTV 24h", b"panel_t_iptv1"), Button.inline(f"{E['tv']} IPTV 48h", b"panel_t_iptv2")],
            [Button.inline(f"{E['p2p']} P2P 24h", b"panel_t_p2p1"), Button.inline(f"{E['p2p']} P2P 48h", b"panel_t_p2p2")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    if d.startswith("t_"):
        tt = d[2:]
        await event.answer(f"{E['load']}")
        await event.edit(f"{E['load']} Gerando teste...", parse_mode="md")
        info = PainelAPI.test(s, tt)
        if info and "error" not in info:
            label = info.pop("_test_type", tt.upper())
            text = format_panel_result(info, f"Teste {label} Criado", E["ok"])
        elif info and "error" in info:
            text = f"{E['err']} **Falha:** `{info['error']}`"
        else:
            text = f"{E['err']} **Falha** - Sem resposta do painel."
        await event.edit(text, buttons=[
            [Button.inline(f"{E['test']} Outro Teste", b"panel_tests")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # LOGS
    if d == "logs":
        await event.edit(f"{E['log']} **Logs**\n{LINE}\n\nSelecione:", buttons=[
            [Button.inline(f"{E['user']} Login", b"panel_l_login"), Button.inline(f"{E['tv']} Clientes", b"panel_l_clients")],
            [Button.inline(f"{E['rev']} Revendedores", b"panel_l_resellers"), Button.inline(f"{E['credit']} Vendas", b"panel_l_sales")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    if d.startswith("l_"):
        lt = d[2:]
        await event.answer(E["load"])
        logs = PainelAPI.logs(s, lt)
        nm = {"login": "Login", "clients": "Clientes", "resellers": "Revendedores", "sales": "Vendas"}
        title = nm.get(lt, "Logs")
        if not logs:
            await event.edit(f"{E['log']} **{title}**\n\n{E['warn']} Vazio.", buttons=[
                [Button.inline(f"{E['back']} Logs", b"panel_logs"), Button.inline(f"{E['back']} Menu", b"panel_menu")],
            ], parse_mode="md")
            return
        lines = [f"{E['log']} **{title}**\n{LINE}\n"]
        for i, entry in enumerate(logs[:25]):
            if isinstance(entry, dict):
                if "data" in entry:
                    lines.append(f"`{i+1}.` {entry['data']}")
                else:
                    parts = [f"**{k}:** `{v}`" for k, v in entry.items() if v]
                    lines.append(f"`{i+1}.` {' | '.join(parts)}")
            else:
                lines.append(f"`{i+1}.` {entry}")
        lines.append(f"\n{THIN}\n**{min(25,len(logs))}/{len(logs)}** registros")
        await event.edit("\n".join(lines), buttons=[
            [Button.inline(f"{E['refresh']} Atualizar", f"panel_{d}".encode())],
            [Button.inline(f"{E['back']} Logs", b"panel_logs"), Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    # FERRAMENTAS
    if d == "tools":
        await event.edit(f"{E['tool']} **Ferramentas**\n{LINE}", buttons=[
            [Button.inline(f"{E['refresh']} Limpar Cache", b"panel_clr_cache"), Button.inline(f"{E['dash']} Stats", b"panel_dash")],
            [Button.inline(f"{E['conn']} Conexoes", b"panel_connections")],
            [Button.inline(f"{E['back']} Menu", b"panel_menu")],
        ], parse_mode="md")
        return

    if d == "clr_cache":
        sm.clear_cache(uid)
        await event.answer(f"{E['ok']} Cache limpo!", alert=True)
        return

    await event.answer()

# ══════════════════════════════════════════════
#  USERBOT — COMANDOS DO DONO (via userbot)
# ══════════════════════════════════════════════

@userbot.on(events.NewMessage(pattern=r'^[!/]grupos$', outgoing=True))
async def ub_cmd_grupos(event):
    text, buttons = build_groups_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')

@userbot.on(events.CallbackQuery(pattern=r'^grppage:(\d+)$'))
async def ub_callback_page(event):
    me = await userbot.get_me()
    if event.sender_id != me.id:
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_groups_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')

@userbot.on(events.CallbackQuery(pattern=r'^rmgrp:(-?\d+)$'))
async def ub_callback_remove(event):
    me = await userbot.get_me()
    if event.sender_id != me.id:
        return
    gid = int(event.pattern_match.group(1))
    remove_group(gid)
    text, buttons = build_groups_page(0)
    await event.edit(text, buttons=buttons, parse_mode='md')

@userbot.on(events.CallbackQuery(pattern=r'^addgrp$'))
async def ub_callback_add(event):
    me = await userbot.get_me()
    if event.sender_id != me.id:
        return
    await event.answer()
    await event.reply(
        "Envie: `/addgrupo -100123456`\n💡 Nome será detectado automaticamente.",
        parse_mode='md'
    )

@userbot.on(events.CallbackQuery(pattern=r'^noop$'))
async def ub_callback_noop(event):
    await event.answer()

@userbot.on(events.NewMessage(pattern=r'^[!/]addgrupo\s+(-?\d+)(?:\s+(.+))?$', outgoing=True))
async def ub_add_group(event):
    gid = int(event.pattern_match.group(1))
    name = event.pattern_match.group(2)

    if not name:
        try:
            entity = await userbot.get_entity(gid)
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Grupo')
        except Exception:
            name = f"Grupo {gid}"

    name = name.strip()
    added = add_group(gid, name)
    if added:
        await event.reply(f"✅ Grupo **{name}** (`{gid}`) adicionado!", parse_mode='md')
    else:
        await event.reply(f"⚠️ Grupo `{gid}` já cadastrado.", parse_mode='md')

@userbot.on(events.NewMessage(pattern=r'^[!/]id$', outgoing=True))
async def ub_get_id(event):
    chat = await event.get_chat()
    chat_name = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'N/A')
    await event.reply(
        f"🆔 **Chat:** `{event.chat_id}`\n📋 **Nome:** {chat_name}",
        parse_mode='md'
    )

@userbot.on(events.NewMessage(pattern=r'^[!/]help$', outgoing=True))
async def ub_help(event):
    await event.reply(
        "╔══════════════════════════════╗\n"
        "║   📖 COMANDOS DO USERBOT      ║\n"
        "╚══════════════════════════════╝\n"
        "\n"
        "🔹 `/grupos` — Gestão de grupos\n"
        "🔹 `/addgrupo <id>` — Adicionar grupo\n"
        "🔹 `/id` — Ver ID do chat\n"
        "🔹 `/status` — Status\n"
        "🔹 `/help` — Ajuda\n"
        "\n📡 Responda minha mensagem com URL para consultar.\n"
        "📡 Use `@InforUser_Bot URL` em grupos permitidos.\n"
        "\n╚══════════════════════════════╝",
        parse_mode='md'
    )

@userbot.on(events.NewMessage(pattern=r'^[!/]status$', outgoing=True))
async def ub_status(event):
    me = await userbot.get_me()
    groups = load_groups()
    automs = load_automs()
    users = load_users()
    ar = load_autoreply()
    msgs = load_msgs_prontas()
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   📊 STATUS DO SISTEMA        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Userbot + Bot + Painel Online**\n"
        f"👤 {me.first_name} (@{me.username or 'N/A'})\n"
        f"📋 **Grupos:** `{len(groups)}`\n"
        f"💬 **AutoMs:** `{len(automs)}`\n"
        f"📝 **Msgs Prontas:** `{len(msgs)}`\n"
        f"👥 **Usuários:** `{len(users)}`\n"
        f"🔄 **Auto-Reply:** `{'✅' if ar.get('ativo') else '❌'}`\n"
        f"🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
#  INICIALIZAÇÃO (USERBOT + BOT JUNTOS)
# ══════════════════════════════════════════════

async def main():
    await userbot.start(phone=PHONE)
    me = await userbot.get_me()

    print("╔══════════════════════════════════════════════════╗")
    print(f"║   ✅ USERBOT SILVA ONLINE — v{BOT_VERSION}              ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  👤 {me.first_name} (@{me.username or 'N/A'})")
    print(f"  🆔 {me.id}")
    print(f"  📋 Grupos: {len(load_groups())}")
    print(f"  💬 AutoMs: {len(load_automs())}")
    print(f"  📝 Msgs Prontas: {len(load_msgs_prontas())}")
    print(f"  👥 Usuários: {len(load_users())}")
    print("════════════════════════════════════════════════════")

    await bot.start(bot_token=BOT_TOKEN)
    bot_me = await bot.get_me()

    print("╔══════════════════════════════════════════════════╗")
    print(f"║   🤖 BOT SILVA MANAGER + PAINEL ONLINE           ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  🤖 {bot_me.first_name} (@{bot_me.username or 'N/A'})")
    print(f"  🆔 {bot_me.id}")
    print(f"  🔗 Painel: {PAINEL_URL}")
    print("════════════════════════════════════════════════════")
    print()
    print(f"🚀 SILVA MANAGER PRO v{BOT_VERSION} — Sistema completo rodando!")
    print("   Userbot + Bot + Inline + AutoMs + Msgs Prontas")
    print("   AutoReply + Painel IPTV/P2P + Testes + Logs")
    print(f"   👤 Dono: {OWNER_NAME} ({OWNER_ID})")
    print()

    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
