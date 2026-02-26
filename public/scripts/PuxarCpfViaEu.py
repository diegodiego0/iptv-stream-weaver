#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════
# 🤖  BOT INTERAÇÃO + MIGRADOR IPTV v4.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ⚡ Powered by 773H Ultra
# ══════════════════════════════════════════════

import json
import os
import asyncio
import requests
import platform
import ssl
import logging
import threading
import random
import sys
import re
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# ══════════════════════════════════════════════
# 🔒  SSL / REQUESTS CONFIG
# ══════════════════════════════════════════════
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256:TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256:TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256:TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256:TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA:TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA:TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA:TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_AES_128_GCM_SHA256:TLS_RSA_WITH_AES_256_GCM_SHA384:TLS_RSA_WITH_AES_128_CBC_SHA:TLS_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_3DES_EDE_CBC_SHA:TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256:TLS13-AES-256-GCM-SHA384:ECDHE:!COMP:TLS13-AES-256-GCM-SHA384:TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

# ══════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES
# ══════════════════════════════════════════════
API_ID = 29214781                        # Obtenha em https://my.telegram.org
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102                    # Edivaldo Silva @Edkd1

# API de consulta
API_CONSULTA_URL = "https://searchapi.dnnl.live/consulta"
API_CONSULTA_TOKEN = "4150"

FOLDER_PATH = "data"
CONFIG_PATH = os.path.join(FOLDER_PATH, "grupos_config.json")
LOG_PATH = os.path.join(FOLDER_PATH, "bot_interacao.log")
SESSION_USER = "session_monitor"
SESSION_BOT = "session_bot"

ITEMS_PER_PAGE = 8

# ══════════════════════════════════════════════
# 📁  MIGRADOR IPTV — CAMINHOS FIXOS (NÃO ALTERAR)
# ══════════════════════════════════════════════
HOSTS_FILE = "/sdcard/server/hosts.txt"
SAVE_FILE = "/sdcard/hits/7773H_souiptv_migrado.txt"
URLS_FILE = "/sdcard/hits/novas_urls.txt"

migrador_hits = 0
migrador_fails = 0
migrador_lock = threading.Lock()
migrador_primeira_info_salva = False
migrador_em_execucao = False

# ══════════════════════════════════════════════
# 📁  USER-AGENTS ROTATIVOS (MIGRADOR)
# ══════════════════════════════════════════════
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 SamsungBrowser/22.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Brave/1.60",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OPR/105.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (compatible; YandexBrowser/23.9)"
]

# ══════════════════════════════════════════════
# 📁  CONFIGURAÇÃO DE GRUPOS (JSON)
# ══════════════════════════════════════════════
os.makedirs(FOLDER_PATH, exist_ok=True)
os.makedirs("/sdcard/hits", exist_ok=True)

def carregar_config() -> dict:
    """Carrega configuração dos grupos monitorados."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"grupos": {}, "respostas_auto": True}
    return {"grupos": {}, "respostas_auto": True}

def salvar_config(config: dict):
    """Salva configuração dos grupos."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar config: {e}")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except IOError:
        pass

# ══════════════════════════════════════════════
# 🤖  CLIENTES TELETHON
# ══════════════════════════════════════════════
user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot = TelegramClient(SESSION_BOT, API_ID, API_HASH)

def is_admin(user_id: int) -> bool:
    """Verifica se o usuário é o administrador/dono do bot."""
    return user_id == OWNER_ID

# ══════════════════════════════════════════════
# 🔍  CONSULTA CPF (API)
# ══════════════════════════════════════════════

def consultar_cpf(cpf: str) -> str:
    """Consulta CPF na API e retorna texto formatado."""
    params = {
        "token_api": API_CONSULTA_TOKEN,
        "cpf": cpf
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (educational script)",
        "Accept": "application/json"
    }

    try:
        response = requests.get(API_CONSULTA_URL, params=params, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return f"❌ **Erro de conexão com a API**\n`{e}`"

    try:
        data = response.json()
    except json.JSONDecodeError:
        return "⚠️ Resposta da API não está em JSON."

    if response.status_code != 200:
        mensagem = data.get("mensagem", "Erro desconhecido da API")
        return f"❌ **Erro:** {mensagem}"

    if "dados" not in data or not data["dados"]:
        return "❌ Nenhum registro encontrado para este CPF."

    registro = data["dados"][0]

    def s(v):
        return str(v) if v else "Não informado"

    return f"""╔══════════════════════════╗
║  📄 **CONSULTA CPF**       ║
╚══════════════════════════╝

👤 **Nome:** `{s(registro.get('NOME'))}`
🔢 **CPF:** `{s(registro.get('CPF'))}`
📅 **Nascimento:** `{s(registro.get('NASC'))}`
⚧ **Sexo:** `{s(registro.get('SEXO'))}`

👩 **Mãe:** `{s(registro.get('NOME_MAE'))}`
👨 **Pai:** `{s(registro.get('NOME_PAI'))}`

🪪 **RG:** `{s(registro.get('RG'))}`
🏛️ **Órgão Emissor:** `{s(registro.get('ORGAO_EMISSOR'))}`
📍 **UF Emissão:** `{s(registro.get('UF_EMISSAO'))}`

🗳️ **Título Eleitor:** `{s(registro.get('TITULO_ELEITOR'))}`
💰 **Renda:** `{s(registro.get('RENDA'))}`
📱 **SO:** `{s(registro.get('SO'))}`

▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬"""

# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════
async def notificar(texto: str):
    try:
        await bot.send_message(OWNER_ID, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")

# ══════════════════════════════════════════════
# 🎨  INTERFACE — MENUS INLINE
# ══════════════════════════════════════════════

def menu_principal_buttons(user_id: int = 0):
    btns = [
        [Button.inline("🔍 Consultar CPF", b"cmd_consultar"),
         Button.inline("📊 Status", b"cmd_stats")],
    ]
    if is_admin(user_id):
        btns.append(
            [Button.inline("🔄 Migrador IPTV", b"cmd_migrador"),
             Button.inline("📡 Respostas Auto", b"cmd_toggle_auto")]
        )
        btns.append(
            [Button.inline("⚙️ Configurar Grupos", b"cmd_config_grupos"),
             Button.inline("📋 Grupos Ativos", b"cmd_listar_grupos")]
        )
        btns.append(
            [Button.inline("⚙️ Configurações", b"cmd_config")]
        )
    btns.append([Button.inline("ℹ️ Sobre", b"cmd_about")])
    return btns

def voltar_button():
    return [[Button.inline("🔙 Menu Principal", b"cmd_menu")]]

def paginar_buttons(prefix: str, page: int, total_pages: int):
    btns = []
    nav = []
    if page > 0:
        nav.append(Button.inline("◀️ Anterior", f"{prefix}_page_{page - 1}".encode()))
    nav.append(Button.inline(f"📄 {page + 1}/{total_pages}", b"noop"))
    if page < total_pages - 1:
        nav.append(Button.inline("Próxima ▶️", f"{prefix}_page_{page + 1}".encode()))
    btns.append(nav)
    btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])
    return btns

# ══════════════════════════════════════════════
# 📡  AUTO-RESPOSTA EM GRUPOS
# ══════════════════════════════════════════════

def grupo_esta_configurado(chat_id: int) -> bool:
    """Verifica se o grupo está na lista de grupos configurados."""
    config = carregar_config()
    return str(chat_id) in config.get("grupos", {})

def extrair_cpf(texto: str) -> str:
    """Extrai CPF de uma mensagem — com ou sem pontuação.
    Aceita: 123.456.789-00, 123456789-00, 12345678900, etc."""
    # 1) Tenta formato com pontuação: 000.000.000-00
    match = re.search(r'(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2})', texto)
    if match:
        return re.sub(r'[.\-/\s]', '', match.group(1))
    # 2) Tenta 11 dígitos seguidos
    match = re.search(r'(\d{11})', texto)
    if match:
        return match.group(1)
    return ""

async def processar_mencao_grupo(event):
    """Processa menção ao dono em grupo configurado."""
    config = carregar_config()
    if not config.get("respostas_auto", True):
        return

    chat_id = str(event.chat_id)
    if chat_id not in config.get("grupos", {}):
        return

    # Verifica se a mensagem é uma resposta a uma mensagem do dono
    # ou se menciona o dono
    eh_mencao = False

    # Verifica reply
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            if replied and replied.sender_id == OWNER_ID:
                eh_mencao = True
        except Exception:
            pass

    # Verifica menção direta (@username do dono)
    if not eh_mencao and event.mentioned:
        eh_mencao = True

    # Verifica se mencionou por entidades
    if not eh_mencao and event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, 'user_id') and entity.user_id == OWNER_ID:
                eh_mencao = True
                break

    if not eh_mencao:
        return

    # Pessoa mencionou o dono — processar a mensagem
    texto = event.text or ""
    sender = await event.get_sender()
    nome_sender = f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else "Alguém"

    log(f"📩 Menção recebida de {nome_sender} no grupo {chat_id}: {texto[:80]}")

    # Tenta extrair CPF da mensagem
    cpf = extrair_cpf(texto)

    if cpf:
        # Consulta CPF automaticamente
        resultado = consultar_cpf(cpf)
        await event.reply(resultado, parse_mode='md')
        log(f"✅ Consulta CPF automática respondida para {nome_sender}")
    else:
        # Resposta genérica — reconhece a menção
        grupo_config = config["grupos"][chat_id]
        resposta_padrao = grupo_config.get("resposta_padrao", "")

        if resposta_padrao:
            await event.reply(resposta_padrao, parse_mode='md')
        else:
            await event.reply(
                f"👋 Olá **{nome_sender}**!\n\n"
                f"Vi que me mencionou. Como posso ajudar?\n\n"
                f"💡 **Dica:** Envie um CPF (11 dígitos) na mensagem que eu consulto automaticamente.\n\n"
                f"_▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬_",
                parse_mode='md'
            )

# ══════════════════════════════════════════════════════════════════════
# 🔄  MIGRADOR IPTV — FUNÇÕES COMPLETAS (PRESERVADAS 100%)
# ══════════════════════════════════════════════════════════════════════

def migrador_nova_session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return s

def migrador_contar_linhas_hosts():
    if not os.path.exists(HOSTS_FILE):
        return 0
    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())

def migrador_salvar_resultado(texto):
    try:
        with migrador_lock:
            with open(SAVE_FILE, "a", encoding="utf-8") as arq:
                arq.write(texto + "\n")
                arq.flush()
                try:
                    os.fsync(arq.fileno())
                except Exception:
                    pass
    except Exception as e:
        log(f"❌ Erro ao salvar resultado migrador: {e}")

def migrador_dados_completos(userinfo, criado, expira):
    campos = [
        userinfo.get("username"),
        userinfo.get("password"),
        criado,
        expira,
        userinfo.get("max_connections"),
        userinfo.get("active_cons")
    ]
    for c in campos:
        if c is None or str(c).strip() == "" or str(c) == "N/A":
            return False
    return True

def migrador_salvar_estrutura_completa(username, password, criado, expira,
                                       userinfo, serverinfo, server,
                                       url_server, live, vod, series, m3u_link):
    global migrador_primeira_info_salva
    if migrador_primeira_info_salva:
        return

    with migrador_lock:
        if migrador_primeira_info_salva:
            return

        def safe(v): return str(v) if v is not None else "N/A"

        texto = f"""
🟢STATUS: ATIVO
👤USUÁRIO: {username}
🔑SENHA: {password}
📅CRIADO: {criado}
⏰EXPIRA: {expira}
🔗CONEXÕES MAX: {safe(userinfo.get('max_connections'))}
📡CONEXÕES ATIVAS: {safe(userinfo.get('active_cons'))}
📺CANAIS: {live}
🎬FILMES: {vod}
📺SÉRIES: {series}
🌍TIMEZONE: {safe(serverinfo.get('timezone'))}
🕒HORA ATUAL: {safe(serverinfo.get('time_now'))}
🌐HOST: {server}
🔎URL: {url_server}
🔗M3U: {m3u_link}
▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬
"""
        try:
            with open(URLS_FILE, "w", encoding="utf-8") as f:
                f.write(texto)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            migrador_primeira_info_salva = True
        except Exception as e:
            log(f"❌ Erro ao salvar estrutura completa: {e}")

def migrador_salvar_url_estrutura(url_server):
    if not url_server or url_server == "N/A":
        return

    url_server = url_server.strip()

    with migrador_lock:
        if not os.path.exists(URLS_FILE):
            return
        try:
            with open(URLS_FILE, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f if l.strip()]
        except Exception:
            return

        for l in linhas:
            if url_server in l:
                return

        num = 1
        for l in linhas:
            if l.startswith("🔎URL"):
                num += 1

        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔎URL {num}: {url_server}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
        except Exception:
            pass

def migrador_salvar_novo_host(url_server):
    if not url_server or url_server == "N/A":
        return

    url_server = url_server.strip().lower()
    base = url_server.split(":", 1)[0] if ":" in url_server else url_server

    with migrador_lock:
        if not os.path.exists(HOSTS_FILE):
            try:
                os.makedirs(os.path.dirname(HOSTS_FILE), exist_ok=True)
            except Exception:
                pass
            with open(HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(url_server + "\n")
            return

        try:
            with open(HOSTS_FILE, "r", encoding="utf-8") as f:
                hosts = [h.strip().lower() for h in f if h.strip()]
        except Exception:
            hosts = []

        for h in hosts:
            if h.split(":", 1)[0] == base:
                return

        with open(HOSTS_FILE, "a", encoding="utf-8") as f:
            f.write(url_server + "\n")

def migrador_carregar_hosts():
    if not os.path.exists(HOSTS_FILE):
        log("❌ Arquivo hosts não encontrado!")
        return []

    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        hosts = list(dict.fromkeys([h.strip() for h in f if h.strip()]))
    log(f"📡 Servidores carregados: {len(hosts)}")
    return hosts

def migrador_formatar_data(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

def migrador_contar_conteudo(base_url, user, pwd):
    def req(action):
        s = migrador_nova_session()
        try:
            r = s.get(
                f"{base_url}?username={user}&password={pwd}&action={action}",
                timeout=7
            )
            return len(r.json())
        except Exception:
            return 0
        finally:
            s.close()

    return req("get_live_streams"), req("get_vod_streams"), req("get_series")

def migrador_converter_para_player_api(url_original):
    """
    Converte qualquer formato de URL IPTV para o formato player_api.php.
    Suporta: get.php, m3u direto, .m3u8, .ts, player_api.php
    Retorna: (base_url_api, username, password) ou (None, None, None)
    """
    try:
        url_original = url_original.strip()
        url_limpa = url_original.replace("http://", "").replace("https://", "")
        protocolo = "https://" if "https://" in url_original else "http://"

        if "player_api.php" in url_original:
            partes = url_original.split("player_api.php")[0]
            base = partes.rstrip("/")
            if "username=" in url_original and "password=" in url_original:
                params = url_original.split("?")[1] if "?" in url_original else ""
                user = ""
                pwd = ""
                for p in params.split("&"):
                    if p.startswith("username="):
                        user = p.split("=", 1)[1]
                    elif p.startswith("password="):
                        pwd = p.split("=", 1)[1]
                return f"{base}/player_api.php", user, pwd
            return None, None, None

        if "get.php" in url_original:
            partes = url_original.split("get.php")[0]
            base = partes.rstrip("/")
            if "username=" in url_original and "password=" in url_original:
                params = url_original.split("?")[1] if "?" in url_original else ""
                user = ""
                pwd = ""
                for p in params.split("&"):
                    if p.startswith("username="):
                        user = p.split("=", 1)[1]
                    elif p.startswith("password="):
                        pwd = p.split("=", 1)[1]
                return f"{base}/player_api.php", user, pwd
            return None, None, None

        if "/live/" in url_original or "/movie/" in url_original or "/series/" in url_original:
            segmentos = url_limpa.split("/")
            if len(segmentos) >= 4:
                host_port = segmentos[0]
                tipo_idx = -1
                for i, seg in enumerate(segmentos):
                    if seg in ("live", "movie", "series"):
                        tipo_idx = i
                        break
                if tipo_idx >= 0 and len(segmentos) > tipo_idx + 2:
                    user = segmentos[tipo_idx + 1]
                    pwd = segmentos[tipo_idx + 2]
                    base = f"{protocolo}{host_port}"
                    return f"{base}/player_api.php", user, pwd
            return None, None, None

        if ".m3u" in url_original and "username=" in url_original:
            partes = url_original.split("?")[0]
            base = partes.rsplit("/", 1)[0] if "/" in partes else partes
            params = url_original.split("?")[1] if "?" in url_original else ""
            user = ""
            pwd = ""
            for p in params.split("&"):
                if p.startswith("username="):
                    user = p.split("=", 1)[1]
                elif p.startswith("password="):
                    pwd = p.split("=", 1)[1]
            if user and pwd:
                return f"{base}/player_api.php", user, pwd

        return None, None, None

    except Exception:
        return None, None, None

def migrador_obter_stream_base(server, username, password):
    """
    Obtém a URL base do stream (apenas http://servidor:porta).
    """
    s = migrador_nova_session()
    try:
        server_clean = server.replace("http://", "").replace("https://", "")
        base_url = f"http://{server_clean}/player_api.php"

        streams_url = f"{base_url}?username={username}&password={password}&action=get_live_streams"
        try:
            r = s.get(streams_url, timeout=7)
            streams = r.json()
        except Exception:
            return None

        if not streams or not isinstance(streams, list):
            return None

        formatos = ["ts", "m3u8"]

        for stream in streams[:5]:
            stream_id = stream.get("stream_id")
            if not stream_id:
                continue

            for fmt in formatos:
                stream_url = f"http://{server_clean}/live/{username}/{password}/{stream_id}.{fmt}"

                try:
                    r2 = s.get(stream_url, timeout=6, stream=True, allow_redirects=True)
                    url_final = r2.url
                    r2.close()

                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url_final)
                        if parsed.scheme and parsed.hostname:
                            if parsed.port:
                                stream_base_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                            else:
                                stream_base_url = f"{parsed.scheme}://{parsed.hostname}"
                            return stream_base_url
                    except Exception:
                        url_sem_proto = url_final.split("://", 1)
                        if len(url_sem_proto) == 2:
                            proto = url_sem_proto[0]
                            resto = url_sem_proto[1]
                            servidor_porta = resto.split("/", 1)[0]
                            return f"{proto}://{servidor_porta}"

                except Exception:
                    continue

        return None

    except Exception:
        return None
    finally:
        s.close()

def migrador_salvar_url_base_estrutura(stream_base):
    """
    Salva a URL base do stream no arquivo novas_urls.txt
    com numeração sequencial: 🔰 URL BASE 1: http://...
    """
    if not stream_base or stream_base == "N/A":
        return

    stream_base = stream_base.strip()

    with migrador_lock:
        if not os.path.exists(URLS_FILE):
            return

        try:
            with open(URLS_FILE, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f if l.strip()]
        except Exception:
            return

        for l in linhas:
            if stream_base in l:
                return

        num = 1
        for l in linhas:
            if l.startswith("🔰 URL BASE"):
                num += 1

        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔰URL BASE BD {num}: {stream_base}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            log(f"🔰 URL BASE {num} salva: {stream_base}")
        except Exception:
            pass

def migrador_testar_servidor(server, username, password):
    """Testa um servidor IPTV — função principal do migrador."""
    global migrador_hits, migrador_fails

    server = server.replace("http://", "").replace("https://", "")
    base_url = f"http://{server}/player_api.php"
    auth_url = f"{base_url}?username={username}&password={password}"

    total_hosts = migrador_contar_linhas_hosts()
    log(f"🔄 MIGRAÇÃO EM: {server} | HITS: {migrador_hits} | OFF: {migrador_fails} | HOSTS: {total_hosts}")

    s = migrador_nova_session()
    try:
        r = s.get(auth_url, timeout=8)
        data = r.json()
    except Exception:
        with migrador_lock:
            migrador_fails += 1
        return None
    finally:
        s.close()

    if "user_info" not in data or data["user_info"].get("auth") != 1:
        with migrador_lock:
            migrador_fails += 1
        return None

    with migrador_lock:
        migrador_hits += 1

    userinfo = data["user_info"]
    serverinfo = data.get("server_info", {})
    criado = migrador_formatar_data(userinfo.get("created_at", 0))
    expira = migrador_formatar_data(userinfo.get("exp_date", 0))
    live, vod, series = migrador_contar_conteudo(base_url, username, password)
    url_server = serverinfo.get("url", "N/A")

    migrador_salvar_novo_host(url_server)

    def safe(v): return str(v) if v is not None else "N/A"

    m3u_link = f"http://{server}/get.php?username={safe(userinfo.get('username'))}&password={safe(userinfo.get('password'))}&type=m3u"

    # NOVA LÓGICA PARA novas_urls.txt
    if migrador_dados_completos(userinfo, criado, expira):
        migrador_salvar_estrutura_completa(
            username, password, criado, expira,
            userinfo, serverinfo, server,
            url_server, live, vod, series, m3u_link
        )
        migrador_salvar_url_estrutura(url_server)

    # Obter stream base URL
    log(f"  🔍 Obtendo URL base do stream para {server}...")
    stream_base = migrador_obter_stream_base(server, username, password)
    if stream_base:
        log(f"  🔰 URL BASE: {stream_base}")
        migrador_salvar_url_base_estrutura(stream_base)
    else:
        log(f"  ⚠️ Não foi possível obter URL base de {server}")

    # Texto para salvar no arquivo principal
    texto_resultado = f"""
🟢STATUS: ATIVO
👤USUÁRIO: {username}
🔑SENHA: {password}
📅CRIADO: {criado}
⏰EXPIRA: {expira}
🔗CONEXÕES MAX: {safe(userinfo.get('max_connections'))}
📡CONEXÕES ATIVAS: {safe(userinfo.get('active_cons'))}
📺CANAIS: {live}
🎬FILMES: {vod}
📺SÉRIES: {series}
🌍TIMEZONE: {safe(serverinfo.get('timezone'))}
🕒HORA ATUAL: {safe(serverinfo.get('time_now'))}
🌐HOST: {server}
🔎URL: {url_server}
🔗M3U: {m3u_link}"""

    if stream_base:
        texto_resultado += f"\n🔰 URL BASE: {stream_base}"

    texto_resultado += "\n▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬\n"

    migrador_salvar_resultado(texto_resultado)

    # Retorna dados para notificação no Telegram
    return {
        "server": server,
        "username": safe(userinfo.get('username')),
        "password": safe(userinfo.get('password')),
        "criado": criado,
        "expira": expira,
        "max_conn": safe(userinfo.get('max_connections')),
        "active_conn": safe(userinfo.get('active_cons')),
        "live": live,
        "vod": vod,
        "series": series,
        "url_server": url_server,
        "m3u_link": m3u_link,
        "stream_base": stream_base
    }

def migrador_worker(lista, user, pwd, resultados):
    """Worker thread do migrador."""
    for srv in lista:
        resultado = migrador_testar_servidor(srv, user, pwd)
        if resultado:
            with migrador_lock:
                resultados.append(resultado)

async def executar_migracao_telegram(chat_id, username, password):
    """Executa migração IPTV e reporta via Telegram."""
    global migrador_hits, migrador_fails, migrador_primeira_info_salva, migrador_em_execucao

    if migrador_em_execucao:
        await bot.send_message(chat_id,
            "⚠️ **Migração já em execução!**\n\nAguarde a conclusão da migração atual.",
            parse_mode='md'
        )
        return

    migrador_em_execucao = True
    migrador_hits = 0
    migrador_fails = 0
    migrador_primeira_info_salva = False

    hosts = migrador_carregar_hosts()
    if not hosts:
        await bot.send_message(chat_id,
            f"❌ **Arquivo hosts não encontrado!**\n\n📁 Caminho: `{HOSTS_FILE}`\n\n"
            f"Crie o arquivo com os servidores (um por linha).",
            parse_mode='md'
        )
        migrador_em_execucao = False
        return

    await bot.send_message(chat_id,
        f"""╔══════════════════════════════╗
║  🔄 **MIGRAÇÃO IPTV INICIADA**  ║
╚══════════════════════════════╝

📡 **Servidores:** {len(hosts)}
👤 **User/Pass:** `{username}:{password}`
📁 **Hosts:** `{HOSTS_FILE}`
💾 **Saída:** `{SAVE_FILE}`

⏳ _Processando... Aguarde._

━━━━━━━━━━━━━━━━━━━━━
_▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬_""",
        parse_mode='md'
    )

    # Executar em threads (mesmo esquema do original)
    resultados = []
    partes = 10
    tamanho = max(1, len(hosts) // partes)
    threads = []

    for i in range(partes):
        bloco = hosts[i * tamanho:(i + 1) * tamanho]
        if bloco:
            t = threading.Thread(target=migrador_worker, args=(bloco, username, password, resultados))
            t.start()
            threads.append(t)

    resto = hosts[partes * tamanho:]
    if resto:
        t = threading.Thread(target=migrador_worker, args=(resto, username, password, resultados))
        t.start()
        threads.append(t)

    # Aguardar threads em background sem bloquear o event loop
    def aguardar_threads():
        for t in threads:
            t.join()

    await asyncio.get_event_loop().run_in_executor(None, aguardar_threads)

    # Relatório final
    total_hits = migrador_hits
    total_fails = migrador_fails

    # Enviar resumo dos primeiros 5 hits
    resumo_hits = ""
    for i, r in enumerate(resultados[:5], 1):
        stream_info = f"\n   🔰 Base: `{r['stream_base']}`" if r.get('stream_base') else ""
        resumo_hits += f"""
**{i}.** `{r['server']}`
   👤 `{r['username']}:{r['password']}`
   📅 Expira: `{r['expira']}`
   📺 Live: {r['live']} | 🎬 VOD: {r['vod']} | 📺 Séries: {r['series']}{stream_info}
"""

    if not resumo_hits:
        resumo_hits = "\n_Nenhum hit encontrado._\n"

    await bot.send_message(chat_id,
        f"""╔══════════════════════════════╗
║  ✅ **MIGRAÇÃO FINALIZADA!**    ║
╚══════════════════════════════╝

📊 **Resultado:**
├ ✅ Hits: **{total_hits}**
├ ❌ Fails: **{total_fails}**
└ 📡 Total: **{total_hits + total_fails}**

📋 **Primeiros Hits:**
{resumo_hits}
💾 **Arquivos:**
├ `{SAVE_FILE}`
└ `{URLS_FILE}`

━━━━━━━━━━━━━━━━━━━━━
_▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬_""",
        parse_mode='md',
        buttons=voltar_button()
    )

    migrador_em_execucao = False

# ══════════════════════════════════════════════
# 🎮  HANDLERS DO BOT
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    sender = await event.get_sender()
    uid = sender.id if sender else 0
    await event.respond(
        f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

Bem-vindo ao bot de interação pessoal!

🔍 **Consulte** CPF diretamente
🔄 **Migrador** IPTV integrado
⚙️ **Configure** grupos para auto-resposta
📡 **Responda** automaticamente quando citado

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: Edivaldo Silva @Edkd1_
⚡ _Powered by 773H Ultra_
━━━━━━━━━━━━━━━━━━━━━

Selecione uma opção abaixo:""",
        parse_mode='md',
        buttons=menu_principal_buttons(uid)
    )

@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await cmd_start(event)

# ══════════════════════════════════════════════
# 🔘  HANDLERS DE CALLBACK (BOTÕES INLINE)
# ══════════════════════════════════════════════

# Estados temporários por chat
pending_action = {}

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    try:
        message = await event.get_message()

        # ── Menu Principal ──
        if data == "cmd_menu":
            await message.edit(
                f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Consultar CPF ──
        elif data == "cmd_consultar":
            pending_action[chat_id] = "aguardando_cpf"
            await message.edit(
                """🔍 **Modo Consulta CPF**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie o CPF** (apenas números):

• Exemplo: `12345678900`
• Ou com pontuação: `123.456.789-00`

━━━━━━━━━━━━━━━━━━━━━
_Aguardando CPF..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Migrador IPTV ──
        elif data == "cmd_migrador":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            total_hosts = migrador_contar_linhas_hosts()
            status_exec = "🔴 Em execução" if migrador_em_execucao else "🟢 Disponível"

            pending_action[chat_id] = "aguardando_credencial_migrador"
            await message.edit(
                f"""╔══════════════════════════════╗
║  🔄 **MIGRADOR IPTV**           ║
╚══════════════════════════════╝

📡 **Servidores no hosts:** {total_hosts}
📁 **Arquivo:** `{HOSTS_FILE}`
⚙️ **Status:** {status_exec}

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie as credenciais** no formato:

`user:pass`

━━━━━━━━━━━━━━━━━━━━━
_Aguardando credenciais..._
_▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Status ──
        elif data == "cmd_stats":
            config = carregar_config()
            total_grupos = len(config.get("grupos", {}))
            auto_ativo = "✅ Ativo" if config.get("respostas_auto", True) else "❌ Desativado"
            total_hosts = migrador_contar_linhas_hosts()
            migrador_status = "🔴 Executando" if migrador_em_execucao else "🟢 Parado"

            await message.edit(
                f"""╔══════════════════════════╗
║  📊 **STATUS DO BOT**      ║
╚══════════════════════════╝

🤖 **Bot Interação v4.0**

📡 **Grupos Configurados:** **{total_grupos}**
🔄 **Auto-Resposta:** {auto_ativo}
🔍 **API Consulta:** Ativa

🔄 **Migrador IPTV:**
├ Status: {migrador_status}
├ Hosts: **{total_hosts}**
├ Hits: **{migrador_hits}**
└ Fails: **{migrador_fails}**

⚙️ **Sistema:**
├ 💾 Config: `{CONFIG_PATH}`
├ 📝 Logs: `{LOG_PATH}`
└ 🕐 Uptime: `Ativo`

_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Configurar Grupos (ADMIN) ──
        elif data == "cmd_config_grupos":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            await message.edit(
                """⚙️ **Configurar Grupos**

━━━━━━━━━━━━━━━━━━━━━
Escolha uma ação:

• **Adicionar** — Cadastra um grupo pelo ID
• **Remover** — Remove grupo da lista
• **Resposta** — Define resposta padrão

━━━━━━━━━━━━━━━━━━━━━
_Grupos configurados receberão auto-resposta quando você for citado._""",
                parse_mode='md',
                buttons=[
                    [Button.inline("➕ Adicionar Grupo", b"cmd_add_grupo"),
                     Button.inline("➖ Remover Grupo", b"cmd_rem_grupo")],
                    [Button.inline("💬 Definir Resposta Padrão", b"cmd_set_resposta")],
                    [Button.inline("📋 Ver Grupos Ativos", b"cmd_listar_grupos")],
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ]
            )

        # ── Adicionar Grupo ──
        elif data == "cmd_add_grupo":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return
            pending_action[chat_id] = "aguardando_grupo_id"
            await message.edit(
                """➕ **Adicionar Grupo**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie o ID do grupo** (número negativo):

• Exemplo: `-1001234567890`
• Ou encaminhe uma mensagem do grupo

💡 Para descobrir o ID, adicione o bot ao grupo e use `/id` lá.

━━━━━━━━━━━━━━━━━━━━━
_Aguardando ID do grupo..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Remover Grupo ──
        elif data == "cmd_rem_grupo":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "❌ **Nenhum grupo configurado.**\n\nAdicione um grupo primeiro.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            btns = []
            for gid, info in grupos.items():
                nome = info.get("nome", gid)
                btns.append([Button.inline(f"🗑️ {nome} ({gid})", f"remover_{gid}".encode())])
            btns.append([Button.inline("🔙 Voltar", b"cmd_config_grupos")])

            await message.edit(
                "➖ **Selecione o grupo para remover:**",
                parse_mode='md',
                buttons=btns
            )

        # ── Confirmar remoção ──
        elif data.startswith("remover_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            gid = data.replace("remover_", "")
            config = carregar_config()
            grupos = config.get("grupos", {})

            if gid in grupos:
                nome = grupos[gid].get("nome", gid)
                del grupos[gid]
                config["grupos"] = grupos
                salvar_config(config)
                log(f"➖ Grupo removido: {nome} ({gid})")
                await message.edit(
                    f"✅ **Grupo removido com sucesso!**\n\n🗑️ `{nome}` (`{gid}`)",
                    parse_mode='md',
                    buttons=voltar_button()
                )
            else:
                await event.answer("❌ Grupo não encontrado.", alert=True)

        # ── Definir Resposta Padrão ──
        elif data == "cmd_set_resposta":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "❌ **Nenhum grupo configurado.**\n\nAdicione um grupo primeiro.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            btns = []
            for gid, info in grupos.items():
                nome = info.get("nome", gid)
                btns.append([Button.inline(f"💬 {nome}", f"setresp_{gid}".encode())])
            btns.append([Button.inline("🔙 Voltar", b"cmd_config_grupos")])

            await message.edit(
                "💬 **Selecione o grupo para definir resposta padrão:**\n\n"
                "_A resposta padrão é enviada quando você é citado mas não há CPF na mensagem._",
                parse_mode='md',
                buttons=btns
            )

        elif data.startswith("setresp_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            gid = data.replace("setresp_", "")
            pending_action[chat_id] = f"aguardando_resposta_{gid}"

            config = carregar_config()
            resp_atual = config.get("grupos", {}).get(gid, {}).get("resposta_padrao", "Nenhuma definida")

            await message.edit(
                f"💬 **Definir Resposta Padrão**\n\n"
                f"📍 Grupo: `{gid}`\n"
                f"📝 Atual: _{resp_atual}_\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Envie a nova resposta padrão:**\n\n"
                f"_Suporta Markdown. Envie `limpar` para remover._",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Toggle Auto-Resposta ──
        elif data == "cmd_toggle_auto":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            config["respostas_auto"] = not config.get("respostas_auto", True)
            salvar_config(config)

            estado = "✅ Ativado" if config["respostas_auto"] else "❌ Desativado"
            await event.answer(f"Auto-resposta: {estado}", alert=True)
            # Atualiza menu
            await message.edit(
                f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

🔄 Auto-resposta: **{estado}**

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Listar Grupos ──
        elif data == "cmd_listar_grupos":
            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "📋 **Nenhum grupo configurado.**\n\n"
                    "Use ⚙️ Configurar Grupos para adicionar.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            text = "📋 **Grupos Configurados:**\n\n"
            for i, (gid, info) in enumerate(grupos.items(), 1):
                nome = info.get("nome", "Sem nome")
                resp = info.get("resposta_padrao", "Padrão")
                adicionado = info.get("adicionado_em", "N/A")
                text += f"**{i}.** `{nome}`\n"
                text += f"   🔢 ID: `{gid}`\n"
                text += f"   💬 Resposta: _{resp[:30] if resp else 'Padrão'}{'...' if resp and len(resp) > 30 else ''}_\n"
                text += f"   📅 Desde: `{adicionado}`\n\n"

            auto = "✅" if config.get("respostas_auto", True) else "❌"
            text += f"🔄 Auto-resposta: {auto}"

            await message.edit(text, parse_mode='md', buttons=[
                [Button.inline("⚙️ Configurar", b"cmd_config_grupos")],
                [Button.inline("🔙 Menu Principal", b"cmd_menu")]
            ])

        # ── Configurações ──
        elif data == "cmd_config":
            config = carregar_config()
            auto = "✅ Ativo" if config.get("respostas_auto", True) else "❌ Desativado"
            total_grupos = len(config.get("grupos", {}))

            await message.edit(
                f"""⚙️ **Configurações Atuais**

━━━━━━━━━━━━━━━━━━━━━
🔄 Auto-resposta: **{auto}**
📡 Grupos configurados: **{total_grupos}**
🔍 API Token: `{API_CONSULTA_TOKEN}`
💾 Config: `{CONFIG_PATH}`
📝 Logs: `{LOG_PATH}`
━━━━━━━━━━━━━━━━━━━━━

_Para alterar token da API, edite as constantes no código._
_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Sobre ──
        elif data == "cmd_about":
            await message.edit(
                """╔══════════════════════════════╗
║  ℹ️ **SOBRE O BOT**           ║
╚══════════════════════════════╝

🤖 **Bot Interação v4.0**
_Bot pessoal de interação, consulta e migração IPTV_

━━━━━━━━━━━━━━━━━━━━━
**Funcionalidades:**
• 🔍 Consulta CPF via API
• 🔄 Migrador IPTV Multi-Server
• ⚙️ Configuração de grupos
• 📡 Auto-resposta quando citado
• 💬 Respostas personalizadas por grupo
• 📊 Status e configurações
• 🔰 Extração de URL Base do Stream

**Como funciona a auto-resposta:**
1. Configure um grupo pelo ID
2. Quando alguém te citar no grupo:
   - Se enviar CPF → Consulta automática
   - Sem CPF → Resposta padrão definida

**Como funciona o Migrador:**
1. Clique em 🔄 Migrador IPTV
2. Envie `user:pass`
3. O bot testa todos os servidores do hosts.txt
4. Resultados salvos em /sdcard/hits/

**Tecnologia:**
• ⚡ Telethon (asyncio)
• 🔍 API de consulta integrada
• 🔄 Migrador multi-thread
• 💾 Config JSON local

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 **Criado por:** Edivaldo Silva
📱 **Contato:** @Edkd1
🔖 **Versão:** 4.0 (773H Ultra)
━━━━━━━━━━━━━━━━━━━━━""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Noop ──
        elif data == "noop":
            await event.answer()

        else:
            await event.answer("⚠️ Ação não reconhecida.")

        try:
            await event.answer()
        except:
            pass

    except Exception as e:
        log(f"❌ Callback error: {e}")
        try:
            await event.answer("❌ Erro interno.")
        except:
            pass

# ══════════════════════════════════════════════
# 💬  HANDLER: TEXTO LIVRE (PRIVADO)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def text_handler(event):
    chat_id = event.chat_id
    texto = event.text.strip()

    action = pending_action.get(chat_id)

    # ── Aguardando CPF ──
    if action == "aguardando_cpf":
        del pending_action[chat_id]
        cpf = re.sub(r'[.\-/\s]', '', texto)

        if not cpf.isdigit() or len(cpf) != 11:
            await event.reply(
                "❌ **CPF inválido.**\n\nEnvie 11 dígitos numéricos.\nExemplo: `12345678900`",
                parse_mode='md',
                buttons=voltar_button()
            )
            return

        await event.reply("🔍 **Consultando...**", parse_mode='md')
        resultado = consultar_cpf(cpf)
        await event.reply(resultado, parse_mode='md', buttons=voltar_button())

    # ── Aguardando credenciais do Migrador IPTV ──
    elif action == "aguardando_credencial_migrador":
        del pending_action[chat_id]

        if ":" not in texto:
            await event.reply(
                "❌ **Formato inválido.**\n\nEnvie no formato: `user:pass`\nExemplo: `admin:12345`",
                parse_mode='md',
                buttons=[
                    [Button.inline("🔄 Tentar Novamente", b"cmd_migrador")],
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ]
            )
            return

        user, pwd = texto.split(":", 1)
        user = user.strip()
        pwd = pwd.strip()

        if not user or not pwd:
            await event.reply(
                "❌ **Credenciais vazias.**\n\nEnvie no formato: `user:pass`",
                parse_mode='md',
                buttons=voltar_button()
            )
            return

        # Iniciar migração em background
        log(f"🔄 Migração iniciada por {event.sender_id}: {user}:***")
        asyncio.create_task(executar_migracao_telegram(chat_id, user, pwd))

    # ── Aguardando ID do grupo ──
    elif action == "aguardando_grupo_id":
        del pending_action[chat_id]
        grupo_id = re.sub(r'[^\d\-]', '', texto)

        if not grupo_id or not grupo_id.lstrip('-').isdigit():
            await event.reply(
                "❌ **ID inválido.**\n\nEnvie o ID numérico do grupo.\nExemplo: `-1001234567890`",
                parse_mode='md',
                buttons=voltar_button()
            )
            return

        # Tenta obter nome do grupo
        nome_grupo = "Grupo"
        try:
            entity = await user_client.get_entity(int(grupo_id))
            nome_grupo = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or "Grupo"
        except Exception:
            pass

        config = carregar_config()
        config["grupos"][grupo_id] = {
            "nome": nome_grupo,
            "adicionado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "resposta_padrao": ""
        }
        salvar_config(config)
        log(f"➕ Grupo adicionado: {nome_grupo} ({grupo_id})")

        await event.reply(
            f"✅ **Grupo adicionado com sucesso!**\n\n"
            f"📍 Nome: **{nome_grupo}**\n"
            f"🔢 ID: `{grupo_id}`\n\n"
            f"_Agora quando alguém te citar nesse grupo, o bot responderá automaticamente._",
            parse_mode='md',
            buttons=[
                [Button.inline("💬 Definir Resposta Padrão", f"setresp_{grupo_id}".encode())],
                [Button.inline("🔙 Menu Principal", b"cmd_menu")]
            ]
        )

    # ── Aguardando resposta padrão ──
    elif action and action.startswith("aguardando_resposta_"):
        gid = action.replace("aguardando_resposta_", "")
        del pending_action[chat_id]

        config = carregar_config()
        if gid in config.get("grupos", {}):
            if texto.lower() == "limpar":
                config["grupos"][gid]["resposta_padrao"] = ""
                salvar_config(config)
                await event.reply(
                    "✅ **Resposta padrão removida!**\n\n_O bot usará a resposta genérica._",
                    parse_mode='md',
                    buttons=voltar_button()
                )
            else:
                config["grupos"][gid]["resposta_padrao"] = texto
                salvar_config(config)
                await event.reply(
                    f"✅ **Resposta padrão definida!**\n\n"
                    f"📍 Grupo: `{gid}`\n"
                    f"💬 Resposta:\n_{texto}_",
                    parse_mode='md',
                    buttons=voltar_button()
                )
        else:
            await event.reply("❌ Grupo não encontrado na config.", buttons=voltar_button())

    # ── Sem ação pendente ──
    else:
        # Tenta interpretar como CPF direto
        cpf = re.sub(r'[.\-/\s]', '', texto)
        if cpf.isdigit() and len(cpf) == 11:
            await event.reply("🔍 **Consultando CPF...**", parse_mode='md')
            resultado = consultar_cpf(cpf)
            await event.reply(resultado, parse_mode='md', buttons=voltar_button())
        # Tenta interpretar como credencial migrador (user:pass)
        elif ":" in texto and is_admin(event.sender_id) and not migrador_em_execucao:
            # Verifica se parece credencial IPTV (sem espaços, formato user:pass)
            partes = texto.split(":", 1)
            if len(partes) == 2 and partes[0].strip() and partes[1].strip() and " " not in partes[0].strip():
                user_m = partes[0].strip()
                pwd_m = partes[1].strip()
                await event.reply(
                    f"🔄 **Credenciais detectadas!**\n\n"
                    f"👤 User: `{user_m}`\n"
                    f"🔑 Pass: `{'*' * len(pwd_m)}`\n\n"
                    f"Deseja iniciar a migração IPTV?",
                    parse_mode='md',
                    buttons=[
                        [Button.inline("✅ Iniciar Migração", f"confirmar_migra_{user_m}:{pwd_m}".encode())],
                        [Button.inline("❌ Cancelar", b"cmd_menu")]
                    ]
                )
            else:
                await event.reply(
                    "💡 Use o menu para navegar ou envie um CPF para consultar.\n\n"
                    "Comandos: /start | /menu | /cpf 12345678900",
                    parse_mode='md',
                    buttons=menu_principal_buttons(event.sender_id)
                )
        else:
            await event.reply(
                "💡 Use o menu para navegar ou envie um CPF para consultar.\n\n"
                "Comandos: /start | /menu | /cpf 12345678900",
                parse_mode='md',
                buttons=menu_principal_buttons(event.sender_id)
            )

# ══════════════════════════════════════════════
# 🔄  HANDLER: CONFIRMAÇÃO DE MIGRAÇÃO VIA BOTÃO
# ══════════════════════════════════════════════

@bot.on(events.CallbackQuery(pattern=b'confirmar_migra_'))
async def confirmar_migracao(event):
    if not is_admin(event.sender_id):
        await event.answer("🔒 Apenas o administrador.", alert=True)
        return

    data = event.data.decode()
    cred = data.replace("confirmar_migra_", "")
    if ":" not in cred:
        await event.answer("❌ Credenciais inválidas.", alert=True)
        return

    user, pwd = cred.split(":", 1)
    chat_id = event.chat_id

    try:
        message = await event.get_message()
        await message.edit(
            "⏳ **Migração iniciando...**\n\n_Aguarde os resultados._",
            parse_mode='md'
        )
    except:
        pass

    log(f"🔄 Migração confirmada por {event.sender_id}: {user}:***")
    asyncio.create_task(executar_migracao_telegram(chat_id, user, pwd))

# ══════════════════════════════════════════════
# 📡  HANDLER: MENSAGENS EM GRUPOS (USER CLIENT)
# ══════════════════════════════════════════════

@user_client.on(events.NewMessage(func=lambda e: e.is_group or e.is_channel))
async def grupo_handler(event):
    """Detecta menções ao dono em grupos configurados."""
    try:
        await processar_mencao_grupo(event)
    except Exception as e:
        log(f"⚠️ Erro no handler de grupo: {e}")

# ══════════════════════════════════════════════
# 🆔  COMANDO /id EM GRUPOS
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/id'))
async def cmd_id(event):
    """Retorna o ID do chat atual."""
    await event.reply(
        f"🔢 **ID deste chat:** `{event.chat_id}`\n\n"
        f"_Use este ID para configurar o grupo no bot._",
        parse_mode='md'
    )

# ══════════════════════════════════════════════
# 🔍  COMANDO /cpf DIRETO
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/cpf\s+(.+)'))
async def cmd_cpf_direto(event):
    """Consulta CPF diretamente via comando."""
    texto = event.pattern_match.group(1).strip()
    cpf = re.sub(r'[.\-/\s]', '', texto)

    if not cpf.isdigit() or len(cpf) != 11:
        await event.reply(
            "❌ **CPF inválido.**\nUse: `/cpf 12345678900`",
            parse_mode='md'
        )
        return

    await event.reply("🔍 **Consultando...**", parse_mode='md')
    resultado = consultar_cpf(cpf)
    await event.reply(resultado, parse_mode='md', buttons=voltar_button())

# ══════════════════════════════════════════════
# 🔄  COMANDO /migrar DIRETO
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/migrar\s+(.+)'))
async def cmd_migrar_direto(event):
    """Inicia migração IPTV diretamente via comando."""
    if not is_admin(event.sender_id):
        await event.reply("🔒 Apenas o administrador.", parse_mode='md')
        return

    texto = event.pattern_match.group(1).strip()
    if ":" not in texto:
        await event.reply(
            "❌ **Formato inválido.**\nUse: `/migrar user:pass`",
            parse_mode='md'
        )
        return

    user, pwd = texto.split(":", 1)
    log(f"🔄 Migração via /migrar por {event.sender_id}: {user}:***")
    asyncio.create_task(executar_migracao_telegram(event.chat_id, user.strip(), pwd.strip()))

# ══════════════════════════════════════════════
# 🚀  MAIN
# ══════════════════════════════════════════════

async def main():
    await user_client.start(PHONE)
    await bot.start(bot_token=BOT_TOKEN)

    log("🚀 Bot Interação + Migrador IPTV v4.0 iniciado!")
    log("👨‍💻 Créditos: Edivaldo Silva @Edkd1")

    config = carregar_config()
    total_grupos = len(config.get("grupos", {}))
    auto = "Ativo" if config.get("respostas_auto", True) else "Desativado"
    total_hosts = migrador_contar_linhas_hosts()
    log(f"📡 Grupos configurados: {total_grupos}")
    log(f"🔄 Auto-resposta: {auto}")
    log(f"📡 Hosts IPTV: {total_hosts}")

    await notificar(
        f"🚀 **Bot Interação + Migrador v4.0 iniciado!**\n\n"
        f"📡 Grupos: **{total_grupos}**\n"
        f"🔄 Auto-resposta: **{auto}**\n"
        f"📡 Hosts IPTV: **{total_hosts}**\n\n"
        f"_Use /start para acessar o menu._\n"
        f"_Use /migrar user:pass para migrar._"
    )

    print("✅ Bot ativo! Use /start, /cpf, /id ou /migrar")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
