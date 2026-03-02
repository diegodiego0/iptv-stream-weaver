#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════╗
║     USERBOT SILVA + BOT ADMIN        ║
║  Consulta IPTV + Gestão de Grupos    ║
║  Inline Mode + AutoMs               ║
╚══════════════════════════════════════╝
"""

import os
import re
import sys
import json
import math
import random
import socket
import asyncio
import hashlib
import requests
from io import StringIO
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from requests.sessions import Session

from telethon import TelegramClient, events, Button
from telethon.tl.types import InputBotInlineResult, InputBotInlineMessageText
from telethon.errors import UserNotParticipantError

# ══════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════

API_ID = 29214781
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"  # Token do @BotFather
OWNER_ID = 2061557102  # Seu ID do Telegram

CANAL_RESULTADOS_ID = -1003774905088
GRUPOS_FILE = "/sdcard/EuBot/grupos_permitidos.txt"
AUTOMS_FILE = "/sdcard/EuBot/automs.json"
ITEMS_PER_PAGE = 5

# ══════════════════════════════════════
# CLIENTES TELETHON
# ══════════════════════════════════════

# Userbot (conta pessoal)
userbot = TelegramClient("userbot_silva_session", API_ID, API_HASH)

# Bot (via BotFather token)
bot = TelegramClient("bot_silva_session", API_ID, API_HASH)

# ══════════════════════════════════════
# GESTÃO DE GRUPOS PERMITIDOS
# ══════════════════════════════════════

def ensure_dir():
    os.makedirs(os.path.dirname(GRUPOS_FILE), exist_ok=True)

def load_groups():
    ensure_dir()
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
    ensure_dir()
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

# ══════════════════════════════════════
# GESTÃO DE AUTOMS (Mensagens Automáticas)
# ══════════════════════════════════════

def ensure_automs_dir():
    os.makedirs(os.path.dirname(AUTOMS_FILE), exist_ok=True)

def load_automs():
    ensure_automs_dir()
    if not os.path.exists(AUTOMS_FILE):
        save_automs([])
        return []
    try:
        with open(AUTOMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_automs(automs):
    ensure_automs_dir()
    with open(AUTOMS_FILE, "w", encoding="utf-8") as f:
        json.dump(automs, f, ensure_ascii=False, indent=2)

def add_autom(title, message):
    automs = load_automs()
    automs.append({"title": title, "message": message})
    save_automs(automs)
    return len(automs)

def remove_autom(index):
    automs = load_automs()
    if 0 <= index < len(automs):
        removed = automs.pop(index)
        save_automs(automs)
        return removed
    return None

# ══════════════════════════════════════
# FUNÇÕES DE CONSULTA IPTV
# ══════════════════════════════════════

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
        return None, f"❌ Não foi possível resolver o host: {host}"

    if not is_port_open(host, port):
        return None, f"❌ Porta {port} fechada em {host}"

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

# ══════════════════════════════════════
#  USERBOT — CONSULTA VIA REPLY
# ══════════════════════════════════════

URL_PATTERN = r'(https?://[^\s]+)'

@userbot.on(events.NewMessage(incoming=True))
async def handle_incoming_reply(event):
    """Responde consultas quando alguém responde a uma mensagem do userbot."""
    if not event.is_reply:
        return

    replied = await event.get_reply_message()
    if not replied or not replied.out:
        return

    # Verifica se o grupo é permitido
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

    # Envia para o canal
    try:
        channel_msg = (
            f"📨 **Nova Consulta**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} {sender_last} ({user_tag})\n"
            f"🆔 **ID:** `{sender_id}`\n"
            f"💬 **Grupo:** `{event.chat_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"\n{result}"
        )
        await userbot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal: {e}")


@userbot.on(events.NewMessage(outgoing=True))
async def handle_self_reply(event):
    """Permite o próprio dono testar respondendo suas próprias mensagens."""
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


# ══════════════════════════════════════
#  BOT — GESTÃO DE GRUPOS (com paginação)
# ══════════════════════════════════════

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


# ---------- BOT: /start ----------
@bot.on(events.NewMessage(pattern=r'^/start$'))
async def bot_start(event):
    if event.is_private:
        await event.reply(
            "╔══════════════════════════════╗\n"
            "║   🤖 BOT SILVA IPTV           ║\n"
            "╚══════════════════════════════╝\n"
            "\n"
            "Bem-vindo! Sou o bot de consulta IPTV.\n\n"
            "📡 **Modo Inline:** Use `@bot_username URL` em qualquer chat\n"
            "📨 **Privado:** Envie uma URL IPTV aqui para consultar\n"
            "📋 **Comandos:** /help\n"
            "\n╚══════════════════════════════╝",
            parse_mode='md'
        )


# ---------- BOT: /help ----------
@bot.on(events.NewMessage(pattern=r'^/help$'))
async def bot_help(event):
    is_owner = (event.sender_id == OWNER_ID)
    text = (
        "╔══════════════════════════════╗\n"
        "║   📖 COMANDOS DO BOT          ║\n"
        "╚══════════════════════════════╝\n"
        "\n"
        "🔹 `/start` — Menu inicial\n"
        "🔹 `/help` — Esta mensagem\n"
        "🔹 Envie uma **URL IPTV** no privado para consultar\n"
        "🔹 Use **Inline:** `@bot_username URL`\n"
    )
    if is_owner:
        text += (
            "\n"
            "👑 **COMANDOS DO DONO:**\n"
            "🔹 `/grupos` — Painel de gestão de grupos\n"
            "🔹 `/addgrupo <id> <nome>` — Adicionar grupo\n"
            "🔹 `/id` — Ver ID do chat\n"
            "🔹 `/status` — Status do sistema\n"
            "🔹 `/automs` — Gerenciar mensagens automáticas\n"
            "🔹 `/addautom <titulo> | <mensagem>` — Adicionar autom\n"
        )
    text += "\n╚══════════════════════════════╝"
    await event.reply(text, parse_mode='md')


# ---------- BOT: /grupos ----------
@bot.on(events.NewMessage(pattern=r'^/grupos$'))
async def bot_grupos(event):
    if event.sender_id != OWNER_ID:
        await event.reply("⛔ Apenas o dono pode gerenciar grupos.")
        return
    text, buttons = build_groups_page(0)
    await event.reply(text, buttons=buttons, parse_mode='md')


# ---------- BOT: Callback paginação ----------
@bot.on(events.CallbackQuery(pattern=r'^grppage:(\d+)$'))
async def bot_callback_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    page = int(event.pattern_match.group(1))
    text, buttons = build_groups_page(page)
    await event.edit(text, buttons=buttons, parse_mode='md')


# ---------- BOT: Callback remover grupo ----------
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


# ---------- BOT: Callback adicionar prompt ----------
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
        "Envie: `/addgrupo -100123456 Nome do Grupo`\n"
        "\n💡 Use `/id` dentro do grupo para descobrir o ID.",
        parse_mode='md'
    )


@bot.on(events.CallbackQuery(pattern=r'^noop$'))
async def bot_callback_noop(event):
    await event.answer()


# ---------- BOT: /addgrupo ----------
@bot.on(events.NewMessage(pattern=r'^/addgrupo\s+(-?\d+)\s+(.+)$'))
async def bot_add_group(event):
    if event.sender_id != OWNER_ID:
        return
    gid = int(event.pattern_match.group(1))
    name = event.pattern_match.group(2).strip()
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


# ---------- BOT: /id ----------
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


# ---------- BOT: /status ----------
@bot.on(events.NewMessage(pattern=r'^/status$'))
async def bot_status(event):
    if event.sender_id != OWNER_ID:
        return
    groups = load_groups()
    automs = load_automs()
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   📊 STATUS DO SISTEMA        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Bot Online**\n"
        f"📋 **Grupos ativos:** `{len(groups)}`\n"
        f"💬 **AutoMs:** `{len(automs)}`\n"
        f"📡 **Canal:** `{CANAL_RESULTADOS_ID}`\n"
        f"🕐 **Hora:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )


# ══════════════════════════════════════
#  BOT — CONSULTA NO PRIVADO
# ══════════════════════════════════════

@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.raw_text.startswith('/')))
async def bot_private_query(event):
    """Consulta IPTV quando o usuário envia URL no privado do bot."""
    # Verifica se o usuário pertence a algum grupo permitido (ou é o dono)
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
            "Você precisa ser membro de um grupo autorizado para usar este bot.",
            parse_mode='md'
        )
        return

    match = re.search(URL_PATTERN, event.raw_text)
    if not match:
        # Se não é URL, verifica se há AutoMs para responder
        automs = load_automs()
        if automs and event.sender_id != OWNER_ID:
            # Envia todas as mensagens automáticas sequencialmente
            for am in automs:
                await event.reply(
                    f"💬 **{am['title']}**\n\n{am['message']}",
                    parse_mode='md'
                )
            return
        return

    url = match.group(1)
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', '') or ''

    processing_msg = await event.reply(
        f"⏳ **Processando consulta...**\n👤 {sender_name}\n📡 Aguarde...",
        parse_mode='md'
    )

    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        await processing_msg.edit(f"❌ **Falhou**\n\n{error}", parse_mode='md')
        return

    await processing_msg.edit(result, parse_mode='md')

    # Envia para o canal
    try:
        sender_username = getattr(sender, 'username', None)
        user_tag = f"@{sender_username}" if sender_username else f"`{event.sender_id}`"
        channel_msg = (
            f"📨 **Consulta via Bot (Privado)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **De:** {sender_name} ({user_tag})\n"
            f"🆔 **ID:** `{event.sender_id}`\n"
            f"🕐 **Data:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n{result}"
        )
        await bot.send_message(CANAL_RESULTADOS_ID, channel_msg, parse_mode='md')
    except Exception as e:
        print(f"[!] Erro ao enviar ao canal: {e}")


# ══════════════════════════════════════
#  BOT — INLINE MODE
# ══════════════════════════════════════

@bot.on(events.InlineQuery)
async def inline_handler(event):
    """Modo inline: @bot_username URL"""
    query = event.text.strip()

    if not query:
        await event.answer(
            results=[],
            switch_pm="Envie uma URL IPTV para consultar",
            switch_pm_param="start"
        )
        return

    match = re.search(URL_PATTERN, query)
    if not match:
        await event.answer(
            results=[],
            switch_pm="URL inválida. Envie uma URL IPTV válida.",
            switch_pm_param="start"
        )
        return

    url = match.group(1)

    # Verifica se o usuário é permitido
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

    # Executa a consulta
    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, check_url, url)

    if error:
        result_id = hashlib.md5(url.encode()).hexdigest()
        builder = event.builder
        article = builder.article(
            title="❌ Consulta Falhou",
            description=error[:100],
            text=error,
            parse_mode='md'
        )
        await event.answer([article])
        return

    result_id = hashlib.md5(url.encode()).hexdigest()
    builder = event.builder
    article = builder.article(
        title="✅ Resultado IPTV",
        description="Clique para enviar o resultado",
        text=result,
        parse_mode='md'
    )
    await event.answer([article])

    # Envia para o canal
    try:
        sender = await event.get_sender()
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


# ══════════════════════════════════════
#  BOT — AUTOMS (Mensagens Automáticas)
# ══════════════════════════════════════

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
            preview = am['message'][:50] + "..." if len(am['message']) > 50 else am['message']
            text += f"**{i}.** 📌 **{am['title']}**\n   _{preview}_\n\n"

    text += "╚══════════════════════════════╝"

    buttons = []
    for idx, am in enumerate(page_automs):
        real_idx = start + idx
        buttons.append([
            Button.inline(f"👁 Ver: {am['title'][:15]}", data=f"viewautom:{real_idx}"),
            Button.inline(f"🗑 Remover", data=f"rmautom:{real_idx}")
        ])

    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("◀️ Voltar", data=f"autompage:{page - 1}"))
    nav_row.append(Button.inline(f"📄 {page + 1}/{total_pages}", data="noop"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Avançar ▶️", data=f"autompage:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        Button.inline("➕ Adicionar Mensagem", data="addautom_prompt"),
        Button.inline("🔄 Atualizar", data="autompage:0")
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
        await event.answer()
        await event.reply(
            f"╔══════════════════════════════╗\n"
            f"║   📌 AUTOM #{idx + 1}                ║\n"
            f"╚══════════════════════════════╝\n"
            f"\n"
            f"📋 **Título:** {am['title']}\n\n"
            f"💬 **Mensagem:**\n{am['message']}\n"
            f"\n╚══════════════════════════════╝",
            parse_mode='md'
        )
    else:
        await event.answer("❌ Mensagem não encontrada.", alert=True)


@bot.on(events.CallbackQuery(pattern=r'^rmautom:(\d+)$'))
async def bot_callback_remove_autom(event):
    if event.sender_id != OWNER_ID:
        await event.answer("⛔ Sem permissão.", alert=True)
        return
    idx = int(event.pattern_match.group(1))
    removed = remove_autom(idx)
    if removed:
        await event.answer(f"✅ AutoM '{removed['title']}' removida!", alert=True)
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
        "`/addautom Título da Mensagem | Conteúdo completo da mensagem automática`\n"
        "\n"
        "💡 Separe título e mensagem com `|`\n"
        "\n╚══════════════════════════════╝",
        parse_mode='md'
    )


@bot.on(events.NewMessage(pattern=r'^/addautom\s+(.+)$'))
async def bot_add_autom(event):
    if event.sender_id != OWNER_ID:
        return

    text = event.pattern_match.group(1).strip()
    if '|' not in text:
        await event.reply(
            "❌ **Formato inválido!**\n\n"
            "Use: `/addautom Título | Mensagem completa`",
            parse_mode='md'
        )
        return

    parts = text.split('|', 1)
    title = parts[0].strip()
    message = parts[1].strip()

    if not title or not message:
        await event.reply("❌ Título e mensagem não podem estar vazios.", parse_mode='md')
        return

    count = add_autom(title, message)
    await event.reply(
        f"✅ **AutoM adicionada!**\n\n"
        f"📌 **Título:** {title}\n"
        f"💬 **Preview:** {message[:80]}{'...' if len(message) > 80 else ''}\n"
        f"📊 **Total:** `{count}` mensagem(ns)\n\n"
        f"Use /automs para gerenciar.",
        parse_mode='md'
    )


# ══════════════════════════════════════
#  USERBOT — COMANDOS DO DONO (via userbot)
# ══════════════════════════════════════

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
        "Envie: `/addgrupo -100123456 Nome do Grupo`",
        parse_mode='md'
    )

@userbot.on(events.CallbackQuery(pattern=r'^noop$'))
async def ub_callback_noop(event):
    await event.answer()

@userbot.on(events.NewMessage(pattern=r'^[!/]addgrupo\s+(-?\d+)\s+(.+)$', outgoing=True))
async def ub_add_group(event):
    gid = int(event.pattern_match.group(1))
    name = event.pattern_match.group(2).strip()
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
        "🔹 `/addgrupo <id> <nome>` — Adicionar grupo\n"
        "🔹 `/id` — Ver ID do chat\n"
        "🔹 `/status` — Status\n"
        "🔹 `/help` — Ajuda\n"
        "\n📡 Responda minha mensagem com URL para consultar.\n"
        "\n╚══════════════════════════════╝",
        parse_mode='md'
    )

@userbot.on(events.NewMessage(pattern=r'^[!/]status$', outgoing=True))
async def ub_status(event):
    me = await userbot.get_me()
    groups = load_groups()
    automs = load_automs()
    await event.reply(
        f"╔══════════════════════════════╗\n"
        f"║   📊 STATUS DO SISTEMA        ║\n"
        f"╚══════════════════════════════╝\n"
        f"\n"
        f"✅ **Userbot + Bot Online**\n"
        f"👤 {me.first_name} (@{me.username or 'N/A'})\n"
        f"📋 **Grupos:** `{len(groups)}`\n"
        f"💬 **AutoMs:** `{len(automs)}`\n"
        f"📡 **Canal:** `{CANAL_RESULTADOS_ID}`\n"
        f"🕐 `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\n╚══════════════════════════════╝",
        parse_mode='md'
    )


# ══════════════════════════════════════
#  INICIALIZAÇÃO (USERBOT + BOT JUNTOS)
# ══════════════════════════════════════

async def main():
    # Inicia o Userbot (conta pessoal)
    await userbot.start(phone=PHONE)
    me = await userbot.get_me()

    print("╔══════════════════════════════╗")
    print("║   ✅ USERBOT SILVA ONLINE     ║")
    print("╚══════════════════════════════╝")
    print(f"  👤 {me.first_name} (@{me.username or 'N/A'})")
    print(f"  🆔 {me.id}")
    print(f"  📋 Grupos: {len(load_groups())}")
    print(f"  💬 AutoMs: {len(load_automs())}")
    print(f"  📡 Canal: {CANAL_RESULTADOS_ID}")
    print(f"  📂 {GRUPOS_FILE}")
    print("═══════════════════════════════")

    # Inicia o Bot (via token)
    await bot.start(bot_token=BOT_TOKEN)
    bot_me = await bot.get_me()

    print("╔══════════════════════════════╗")
    print("║   🤖 BOT SILVA ONLINE         ║")
    print("╚══════════════════════════════╝")
    print(f"  🤖 {bot_me.first_name} (@{bot_me.username or 'N/A'})")
    print(f"  🆔 {bot_me.id}")
    print("═══════════════════════════════")
    print()
    print("🚀 Sistema completo rodando!")
    print("   Userbot + Bot + Inline + AutoMs")
    print()

    # Roda ambos simultaneamente
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
