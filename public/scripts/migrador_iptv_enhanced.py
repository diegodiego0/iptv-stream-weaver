#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    IPTV MIGRATOR PRO - ENHANCED EDITION                      ║
║                         Versão 2.0.0 - Build 2026.01                         ║
║                                                                              ║
║  Desenvolvido por: Edivaldo                                                  ║
║  Compatível com: Python 3.6+ | QPython | Termux | Android                    ║
║                                                                              ║
║  Funcionalidades:                                                            ║
║  • Migração de servidores IPTV com processamento paralelo                    ║
║  • Geração inteligente de domínios via itertools                             ║
║  • Verificação de disponibilidade via DNS/HTTP (sem whois)                   ║
║  • Processamento intercalado 50/50 (arquivo + gerados)                       ║
║  • Salvamento automático de servidores ativos                                ║
║  • Interface colorida e profissional                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import print_function

import requests
import threading
import os
import sys
import time
import socket
import itertools
import random
import json

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Compatibilidade com colorama (opcional)
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback para sistemas sem colorama
    class FakeFore:
        RED = YELLOW = GREEN = CYAN = MAGENTA = WHITE = BLUE = RESET = ""
    class FakeBack:
        RED = YELLOW = GREEN = CYAN = MAGENTA = WHITE = BLUE = RESET = ""
    class FakeStyle:
        BRIGHT = DIM = RESET_ALL = ""
    Fore = FakeFore()
    Back = FakeBack()
    Style = FakeStyle()

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES GLOBAIS
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "2.0.0"
BUILD_DATE = "2026.01"

# Caminhos dos arquivos
HOSTS_FILE = "/sdcard/server/hosts.txt"
SAVE_FILE = "/sdcard/hits/7773H_souiptv_migrado.txt"
URLS_FILE = "/sdcard/hits/novas_urls.txt"
HOSTS_GERADOS_FILE = "/sdcard/hits/hosts_gerados.txt"
DOMINIOS_DISPONIVEIS_FILE = "/sdcard/hits/dominios_disponiveis.txt"
LOG_FILE = "/sdcard/hits/migrator.log"
STATS_FILE = "/sdcard/hits/stats.json"

# Contadores globais
hits = 0
fails = 0
domains_checked = 0
domains_available = 0
domains_active = 0

# Controles de threading
lock = threading.Lock()
primeira_info_salva = False
running = True

# Configurações de rede
TIMEOUT_REQUEST = 8
TIMEOUT_SOCKET = 5
MAX_RETRIES = 2
MAX_WORKERS = 15

# Criar diretórios necessários
for directory in ["/sdcard/hits", "/sdcard/server", "/sdcard/logs"]:
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS DE LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def log_message(level, message):
    """Registra mensagem no arquivo de log."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = "[{timestamp}] [{level}] {message}\n".format(
            timestamp=timestamp, level=level, message=message
        )
        with lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
    except Exception:
        pass

def log_info(message):
    log_message("INFO", message)

def log_error(message):
    log_message("ERROR", message)

def log_success(message):
    log_message("SUCCESS", message)

# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE DO USUÁRIO
# ══════════════════════════════════════════════════════════════════════════════

def clear_screen():
    """Limpa a tela de forma compatível."""
    try:
        os.system('clear' if os.name != 'nt' else 'cls')
    except Exception:
        print("\n" * 50)

def print_banner():
    """Exibe banner principal do sistema."""
    clear_screen()
    banner = """
{cyan}╔══════════════════════════════════════════════════════════════╗
║{yellow}     ██╗██████╗ ████████╗██╗   ██╗    ██████╗ ██████╗  ██████╗  {cyan}║
║{yellow}     ██║██╔══██╗╚══██╔══╝██║   ██║    ██╔══██╗██╔══██╗██╔═══██╗ {cyan}║
║{yellow}     ██║██████╔╝   ██║   ██║   ██║    ██████╔╝██████╔╝██║   ██║ {cyan}║
║{yellow}     ██║██╔═══╝    ██║   ╚██╗ ██╔╝    ██╔═══╝ ██╔══██╗██║   ██║ {cyan}║
║{yellow}     ██║██║        ██║    ╚████╔╝     ██║     ██║  ██║╚██████╔╝ {cyan}║
║{yellow}     ╚═╝╚═╝        ╚═╝     ╚═══╝      ╚═╝     ╚═╝  ╚═╝ ╚═════╝  {cyan}║
║{white}                    MIGRATOR PRO v{version}                        {cyan}║
╠══════════════════════════════════════════════════════════════╣
║{green}  ◆ Migração Inteligente    ◆ Geração de Domínios            {cyan}║
║{green}  ◆ Verificação Paralela    ◆ Compatível QPython/Termux      {cyan}║
╚══════════════════════════════════════════════════════════════╝{reset}
""".format(
        cyan=Fore.CYAN, yellow=Fore.YELLOW, white=Fore.WHITE,
        green=Fore.GREEN, reset=Style.RESET_ALL if COLORAMA_AVAILABLE else "",
        version=VERSION
    )
    print(banner)

def print_divider(char="═", length=64):
    """Imprime divisor estilizado."""
    print(Fore.CYAN + char * length)

def print_status_bar():
    """Exibe barra de status com contadores."""
    global hits, fails, domains_checked, domains_active
    print("\n" + Fore.CYAN + "╔" + "═" * 62 + "╗")
    status = "║ {green}✓ HITS: {hits:<6}{reset} │ {red}✗ FAILS: {fails:<6}{reset} │ {yellow}◈ VERIFICADOS: {checked:<6}{reset}║".format(
        green=Fore.GREEN, red=Fore.RED, yellow=Fore.YELLOW, reset=Fore.WHITE,
        hits=hits, fails=fails, checked=domains_checked
    )
    print(status)
    print(Fore.CYAN + "╚" + "═" * 62 + "╝\n")

def print_progress(current, total, prefix="Progresso", suffix=""):
    """Exibe barra de progresso."""
    if total == 0:
        return
    percent = (current / float(total)) * 100
    filled = int(30 * current // total)
    bar = "█" * filled + "░" * (30 - filled)
    print("\r{cyan}{prefix}: [{green}{bar}{cyan}] {white}{percent:.1f}% {suffix}".format(
        cyan=Fore.CYAN, green=Fore.GREEN, white=Fore.WHITE,
        prefix=prefix, bar=bar, percent=percent, suffix=suffix
    ), end="")
    sys.stdout.flush()

def print_menu():
    """Exibe menu principal."""
    menu = """
{cyan}╔══════════════════════════════════════════════════════════════╗
║{yellow}                    MENU PRINCIPAL                            {cyan}║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  {white}[1]{green} ◆ Modo Normal                                         {cyan}║
║      {white}Processa apenas hosts do arquivo                       {cyan}║
║                                                              ║
║  {white}[2]{green} ◆ Modo Intercalado (50/50)                            {cyan}║
║      {white}50 do arquivo + 50 gerados simultaneamente              {cyan}║
║                                                              ║
║  {white}[3]{green} ◆ Modo Geração                                        {cyan}║
║      {white}Apenas gera e verifica novos domínios                   {cyan}║
║                                                              ║
║  {white}[4]{green} ◆ Estatísticas                                        {cyan}║
║      {white}Exibe estatísticas de execuções anteriores              {cyan}║
║                                                              ║
║  {white}[5]{green} ◆ Configurações                                       {cyan}║
║      {white}Ajustar parâmetros do sistema                           {cyan}║
║                                                              ║
║  {white}[0]{red} ◆ Sair                                                {cyan}║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""".format(
        cyan=Fore.CYAN, yellow=Fore.YELLOW, white=Fore.WHITE,
        green=Fore.GREEN, red=Fore.RED
    )
    print(menu)

# ══════════════════════════════════════════════════════════════════════════════
# SESSÃO HTTP
# ══════════════════════════════════════════════════════════════════════════════

def nova_session():
    """Cria nova sessão HTTP com headers padrão."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 10; SM-G975F)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache"
    })
    return session

# ══════════════════════════════════════════════════════════════════════════════
# GERADOR DE DOMÍNIOS (itertools)
# ══════════════════════════════════════════════════════════════════════════════

class DomainGenerator:
    """
    Gerador inteligente de domínios IPTV usando itertools.
    Combina prefixos, sufixos, palavras-chave e TLDs para criar
    possíveis domínios de servidores IPTV.
    """
    
    # Prefixos comuns em servidores IPTV
    PREFIXES = [
        "iptv", "tv", "stream", "play", "live", "box", "mega", "super",
        "ultra", "hd", "full", "max", "pro", "vip", "gold", "premium",
        "net", "web", "my", "the", "best", "top", "fast", "smart",
        "cloud", "novo", "new", "brasil", "br", "latino", "mundo"
    ]
    
    # Sufixos/palavras do meio
    SUFFIXES = [
        "tv", "iptv", "play", "stream", "box", "hub", "zone", "plus",
        "pro", "hd", "4k", "online", "server", "host", "panel", "app",
        "cast", "link", "media", "video", "channel", "player", "now"
    ]
    
    # Palavras temáticas
    THEMES = [
        "filmes", "series", "canais", "esportes", "futebol", "movies",
        "sports", "channels", "entertainment", "digital", "tech", "sat"
    ]
    
    # TLDs populares
    TLDS = [
        ".com", ".net", ".tv", ".app", ".online", ".live", ".stream",
        ".club", ".site", ".xyz", ".io", ".co", ".cc", ".me", ".info"
    ]
    
    # Portas comuns
    PORTS = ["", ":80", ":8080", ":8000", ":25461", ":25463", ":8880", ":2095", ":2082"]
    
    def __init__(self):
        self.generated = set()
        self.checked = set()
        self.available = []
        self.active_servers = []
        self._load_cache()
    
    def _load_cache(self):
        """Carrega cache de domínios já verificados."""
        try:
            if os.path.exists(HOSTS_GERADOS_FILE):
                with open(HOSTS_GERADOS_FILE, "r", encoding="utf-8") as f:
                    self.checked = set(line.strip().lower() for line in f if line.strip())
                log_info("Cache carregado: {count} domínios".format(count=len(self.checked)))
        except Exception as e:
            log_error("Erro ao carregar cache: {err}".format(err=str(e)))
    
    def _save_to_cache(self, domain):
        """Salva domínio no cache."""
        try:
            with lock:
                with open(HOSTS_GERADOS_FILE, "a", encoding="utf-8") as f:
                    f.write(domain + "\n")
        except Exception:
            pass
    
    def generate_combinations(self, limit=100):
        """
        Gera combinações de domínios usando itertools.
        
        Estratégias:
        1. prefix + suffix + tld
        2. prefix + theme + tld
        3. prefix + number + tld
        4. word combinations
        """
        domains = []
        
        # Estratégia 1: Prefixo + Sufixo + TLD
        for prefix, suffix in itertools.product(self.PREFIXES[:15], self.SUFFIXES[:10]):
            if prefix != suffix:
                for tld in self.TLDS[:8]:
                    domain = "{prefix}{suffix}{tld}".format(
                        prefix=prefix, suffix=suffix, tld=tld
                    )
                    if domain.lower() not in self.checked:
                        domains.append(domain)
        
        # Estratégia 2: Prefixo + Tema + TLD
        for prefix, theme in itertools.product(self.PREFIXES[:10], self.THEMES[:6]):
            for tld in self.TLDS[:5]:
                domain = "{prefix}{theme}{tld}".format(
                    prefix=prefix, theme=theme, tld=tld
                )
                if domain.lower() not in self.checked:
                    domains.append(domain)
        
        # Estratégia 3: Prefixo + Número + TLD
        numbers = ["1", "2", "3", "4", "5", "10", "100", "123", "365", "2024", "2025", "2026"]
        for prefix in self.PREFIXES[:12]:
            for num in numbers:
                for tld in self.TLDS[:5]:
                    domain = "{prefix}{num}{tld}".format(
                        prefix=prefix, num=num, tld=tld
                    )
                    if domain.lower() not in self.checked:
                        domains.append(domain)
        
        # Estratégia 4: Combinações duplas
        for combo in itertools.combinations(self.PREFIXES[:8], 2):
            for tld in self.TLDS[:4]:
                domain = "{a}{b}{tld}".format(a=combo[0], b=combo[1], tld=tld)
                if domain.lower() not in self.checked:
                    domains.append(domain)
        
        # Randomizar e limitar
        random.shuffle(domains)
        unique_domains = list(dict.fromkeys(domains))[:limit]
        
        log_info("Gerados {count} domínios únicos".format(count=len(unique_domains)))
        return unique_domains
    
    def generate_with_ports(self, domains):
        """Adiciona variações de porta aos domínios."""
        result = []
        for domain in domains:
            for port in self.PORTS:
                result.append(domain + port)
        return result

# ══════════════════════════════════════════════════════════════════════════════
# VERIFICADOR DE DOMÍNIOS (sem whois - compatível com QPython)
# ══════════════════════════════════════════════════════════════════════════════

class DomainChecker:
    """
    Verificador de domínios compatível com QPython/Python 3.6+.
    Usa apenas socket e requests para verificação (sem whois).
    """
    
    def __init__(self):
        self.dns_cache = {}
    
    def check_dns(self, domain):
        """
        Verifica se domínio resolve via DNS.
        Retorna IP ou None.
        """
        # Remove porta se existir
        host = domain.split(":")[0] if ":" in domain else domain
        
        # Cache check
        if host in self.dns_cache:
            return self.dns_cache[host]
        
        try:
            socket.setdefaulttimeout(TIMEOUT_SOCKET)
            ip = socket.gethostbyname(host)
            self.dns_cache[host] = ip
            return ip
        except socket.gaierror:
            self.dns_cache[host] = None
            return None
        except socket.timeout:
            self.dns_cache[host] = None
            return None
        except Exception:
            self.dns_cache[host] = None
            return None
    
    def check_http(self, domain):
        """
        Verifica se servidor HTTP está respondendo.
        Retorna True/False.
        """
        # Limpa domínio
        if not domain.startswith("http"):
            url = "http://{domain}".format(domain=domain)
        else:
            url = domain
        
        session = nova_session()
        try:
            response = session.get(url, timeout=TIMEOUT_REQUEST, allow_redirects=True)
            return response.status_code < 500
        except requests.exceptions.SSLError:
            # Tenta sem SSL
            try:
                url_http = url.replace("https://", "http://")
                response = session.get(url_http, timeout=TIMEOUT_REQUEST)
                return response.status_code < 500
            except Exception:
                return False
        except Exception:
            return False
        finally:
            session.close()
    
    def check_iptv_service(self, domain, test_user="test", test_pass="test"):
        """
        Verifica se é um servidor IPTV ativo.
        Testa endpoint player_api.php
        """
        # Limpa domínio
        host = domain.replace("http://", "").replace("https://", "")
        api_url = "http://{host}/player_api.php?username={user}&password={pwd}".format(
            host=host, user=test_user, pwd=test_pass
        )
        
        session = nova_session()
        try:
            response = session.get(api_url, timeout=TIMEOUT_REQUEST)
            data = response.json()
            
            # Verifica se resposta tem estrutura IPTV
            if "user_info" in data or "server_info" in data:
                return True, data
            return False, None
        except ValueError:
            # Resposta não é JSON mas servidor respondeu
            return False, None
        except Exception:
            return False, None
        finally:
            session.close()
    
    def full_check(self, domain):
        """
        Verificação completa: DNS → HTTP → IPTV
        Retorna dict com resultados.
        """
        global domains_checked
        
        result = {
            "domain": domain,
            "dns_resolved": False,
            "ip": None,
            "http_active": False,
            "iptv_service": False,
            "iptv_data": None
        }
        
        with lock:
            domains_checked += 1
        
        # Passo 1: DNS
        ip = self.check_dns(domain)
        if ip:
            result["dns_resolved"] = True
            result["ip"] = ip
            
            # Passo 2: HTTP
            if self.check_http(domain):
                result["http_active"] = True
                
                # Passo 3: IPTV
                is_iptv, data = self.check_iptv_service(domain)
                if is_iptv:
                    result["iptv_service"] = True
                    result["iptv_data"] = data
        
        return result

# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════════════════════

def salvar_resultado(texto):
    """Salva resultado de migração no arquivo principal."""
    try:
        with lock:
            with open(SAVE_FILE, "a", encoding="utf-8") as arq:
                arq.write(texto + "\n")
                arq.flush()
                try:
                    os.fsync(arq.fileno())
                except Exception:
                    pass
    except Exception as e:
        log_error("Erro ao salvar resultado: {err}".format(err=str(e)))

def dados_completos(userinfo, criado, expira):
    """Valida se dados estão completos."""
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

def salvar_estrutura_completa(username, password, criado, expira,
                              userinfo, serverinfo, server,
                              url_server, live, vod, series, m3u_link):
    """Salva estrutura completa no arquivo novas_urls.txt."""
    global primeira_info_salva
    
    if primeira_info_salva:
        return
    
    with lock:
        if primeira_info_salva:
            return
        
        def safe(v):
            return str(v) if v is not None else "N/A"
        
        texto = """
╔══════════════════════════════════════════════════════════════╗
║                    SERVIDOR IPTV ATIVO                       ║
╠══════════════════════════════════════════════════════════════╣

🟢 STATUS: ATIVO
👤 USUÁRIO: {username}
🔑 SENHA: {password}
📅 CRIADO: {criado}
⏰ EXPIRA: {expira}
🔗 CONEXÕES MAX: {max_conn}
📡 CONEXÕES ATIVAS: {active_conn}
📺 CANAIS: {live}
🎬 FILMES: {vod}
📺 SÉRIES: {series}
🌍 TIMEZONE: {timezone}
🕒 HORA ATUAL: {time_now}
🌐 HOST: {server}
🔎 URL: {url_server}
🔗 M3U: {m3u_link}

▬▬▬ஜ۩ IPTV MIGRATOR PRO ۩ஜ▬▬▬
""".format(
            username=username, password=password, criado=criado, expira=expira,
            max_conn=safe(userinfo.get('max_connections')),
            active_conn=safe(userinfo.get('active_cons')),
            live=live, vod=vod, series=series,
            timezone=safe(serverinfo.get('timezone')),
            time_now=safe(serverinfo.get('time_now')),
            server=server, url_server=url_server, m3u_link=m3u_link
        )
        
        try:
            with open(URLS_FILE, "w", encoding="utf-8") as f:
                f.write(texto)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            primeira_info_salva = True
            log_success("Estrutura completa salva")
        except Exception as e:
            log_error("Erro ao salvar estrutura: {err}".format(err=str(e)))

def salvar_url_estrutura(url_server):
    """Salva URL numerada sem duplicar."""
    if not url_server or url_server == "N/A":
        return
    
    url_server = url_server.strip()
    
    with lock:
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
            if l.startswith("🔎URL") or l.startswith("🔎 URL"):
                num += 1
        
        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write("🔎 URL {num}: {url}\n".format(num=num, url=url_server))
                f.flush()
        except Exception:
            pass

def salvar_novo_host(url_server):
    """Salva novo host descoberto no arquivo hosts.txt."""
    if not url_server or url_server == "N/A":
        return
    
    url_server = url_server.strip().lower()
    base = url_server.split(":")[0] if ":" in url_server else url_server
    
    with lock:
        if not os.path.exists(HOSTS_FILE):
            try:
                os.makedirs(os.path.dirname(HOSTS_FILE), exist_ok=True)
            except Exception:
                pass
            with open(HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(url_server + "\n")
            log_info("Novo host adicionado: {host}".format(host=url_server))
            return
        
        try:
            with open(HOSTS_FILE, "r", encoding="utf-8") as f:
                hosts = [h.strip().lower() for h in f if h.strip()]
        except Exception:
            hosts = []
        
        for h in hosts:
            if h.split(":")[0] == base:
                return
        
        with open(HOSTS_FILE, "a", encoding="utf-8") as f:
            f.write(url_server + "\n")
        log_info("Novo host adicionado: {host}".format(host=url_server))

def salvar_dominio_disponivel(domain, ip=None):
    """Salva domínio disponível para registro."""
    global domains_available
    
    with lock:
        domains_available += 1
        try:
            with open(DOMINIOS_DISPONIVEIS_FILE, "a", encoding="utf-8") as f:
                if ip:
                    f.write("{domain} [{ip}]\n".format(domain=domain, ip=ip))
                else:
                    f.write(domain + "\n")
        except Exception:
            pass

def salvar_servidor_ativo(domain):
    """Salva servidor IPTV ativo encontrado."""
    global domains_active
    
    with lock:
        domains_active += 1
        salvar_novo_host(domain)
        log_success("Servidor IPTV ativo: {domain}".format(domain=domain))

def carregar_hosts():
    """Carrega lista de hosts do arquivo."""
    if not os.path.exists(HOSTS_FILE):
        print(Fore.RED + "\n  ⚠ ERRO: Arquivo hosts não encontrado!")
        print(Fore.YELLOW + "  Caminho: {path}".format(path=HOSTS_FILE))
        return []
    
    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        hosts = list(dict.fromkeys([h.strip() for h in f if h.strip()]))
    
    print(Fore.GREEN + "\n  ✓ Servidores carregados: {count}".format(count=len(hosts)))
    log_info("Hosts carregados: {count}".format(count=len(hosts)))
    return hosts

def salvar_estatisticas():
    """Salva estatísticas da execução."""
    global hits, fails, domains_checked, domains_available, domains_active
    
    stats = {
        "ultima_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hits": hits,
        "fails": fails,
        "dominios_verificados": domains_checked,
        "dominios_disponiveis": domains_available,
        "servidores_ativos": domains_active
    }
    
    try:
        # Carregar stats anteriores se existir
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                old_stats = json.load(f)
                stats["total_hits"] = old_stats.get("total_hits", 0) + hits
                stats["total_verificados"] = old_stats.get("total_verificados", 0) + domains_checked
                stats["execucoes"] = old_stats.get("execucoes", 0) + 1
        else:
            stats["total_hits"] = hits
            stats["total_verificados"] = domains_checked
            stats["execucoes"] = 1
        
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        log_error("Erro ao salvar stats: {err}".format(err=str(e)))

def exibir_estatisticas():
    """Exibe estatísticas salvas."""
    print_banner()
    print(Fore.CYAN + "\n╔══════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║" + Fore.YELLOW + "                      ESTATÍSTICAS                            " + Fore.CYAN + "║")
    print(Fore.CYAN + "╠══════════════════════════════════════════════════════════════╣")
    
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
            
            print(Fore.CYAN + "║" + Fore.WHITE + "  Última execução: {val:<40}".format(val=stats.get("ultima_execucao", "N/A")) + Fore.CYAN + "║")
            print(Fore.CYAN + "║" + Fore.GREEN + "  Total de hits: {val:<42}".format(val=stats.get("total_hits", 0)) + Fore.CYAN + "║")
            print(Fore.CYAN + "║" + Fore.YELLOW + "  Domínios verificados: {val:<35}".format(val=stats.get("total_verificados", 0)) + Fore.CYAN + "║")
            print(Fore.CYAN + "║" + Fore.MAGENTA + "  Total de execuções: {val:<37}".format(val=stats.get("execucoes", 0)) + Fore.CYAN + "║")
        else:
            print(Fore.CYAN + "║" + Fore.RED + "  Nenhuma estatística disponível.                            " + Fore.CYAN + "║")
    except Exception as e:
        print(Fore.CYAN + "║" + Fore.RED + "  Erro ao ler estatísticas: {err:<32}".format(err=str(e)[:32]) + Fore.CYAN + "║")
    
    print(Fore.CYAN + "╚══════════════════════════════════════════════════════════════╝\n")

# ══════════════════════════════════════════════════════════════════════════════
# FORMATAÇÃO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

def formatar_data(ts):
    """Formata timestamp para data legível."""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

def contar_conteudo(base_url, user, pwd):
    """Conta quantidade de conteúdo no servidor."""
    def req(action):
        session = nova_session()
        try:
            url = "{base}?username={user}&password={pwd}&action={action}".format(
                base=base_url, user=user, pwd=pwd, action=action
            )
            r = session.get(url, timeout=TIMEOUT_REQUEST)
            return len(r.json())
        except Exception:
            return 0
        finally:
            session.close()
    
    return req("get_live_streams"), req("get_vod_streams"), req("get_series")

# ══════════════════════════════════════════════════════════════════════════════
# TESTE DE SERVIDOR
# ══════════════════════════════════════════════════════════════════════════════

def testar_servidor(server, username, password, show_output=True):
    """
    Testa servidor IPTV e exibe/salva resultados.
    """
    global hits, fails
    
    # Limpa servidor
    server = server.replace("http://", "").replace("https://", "")
    base_url = "http://{server}/player_api.php".format(server=server)
    auth_url = "{base}?username={user}&password={pwd}".format(
        base=base_url, user=username, pwd=password
    )
    
    if show_output:
        print_status_bar()
        print(Fore.WHITE + "  📡 Testando: " + Fore.CYAN + server)
    
    session = nova_session()
    try:
        response = session.get(auth_url, timeout=TIMEOUT_REQUEST)
        data = response.json()
    except Exception as e:
        with lock:
            fails += 1
        if show_output:
            print(Fore.RED + "  ✗ Falha na conexão")
        return False
    finally:
        session.close()
    
    # Verifica autenticação
    if "user_info" not in data or data["user_info"].get("auth") != 1:
        with lock:
            fails += 1
        if show_output:
            print(Fore.RED + "  ✗ Autenticação falhou")
        return False
    
    # Sucesso!
    with lock:
        hits += 1
    
    userinfo = data["user_info"]
    serverinfo = data.get("server_info", {})
    
    criado = formatar_data(userinfo.get("created_at", 0))
    expira = formatar_data(userinfo.get("exp_date", 0))
    
    live, vod, series = contar_conteudo(base_url, username, password)
    url_server = serverinfo.get("url", "N/A")
    
    salvar_novo_host(url_server)
    
    def safe(v):
        return str(v) if v is not None else "N/A"
    
    m3u_link = "http://{server}/get.php?username={user}&password={pwd}&type=m3u".format(
        server=server, user=safe(userinfo.get('username')), pwd=safe(userinfo.get('password'))
    )
    
    # Salva estrutura se dados completos
    if dados_completos(userinfo, criado, expira):
        salvar_estrutura_completa(
            username, password, criado, expira,
            userinfo, serverinfo, server,
            url_server, live, vod, series, m3u_link
        )
        salvar_url_estrutura(url_server)
    
    # Exibe informações
    if show_output:
        print(Fore.CYAN + "\n  ╔══════════════════════════════════════════════════════════╗")
        print(Fore.CYAN + "  ║" + Fore.GREEN + "          ✓ SERVIDOR ATIVO - MIGRAÇÃO SUCESSO            " + Fore.CYAN + "║")
        print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
        print(Fore.CYAN + "  ║" + Fore.YELLOW + "  👤 Usuário: {val:<42}".format(val=safe(userinfo.get('username'))[:42]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.YELLOW + "  🔑 Senha: {val:<44}".format(val=safe(userinfo.get('password'))[:44]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.WHITE + "  📅 Criação: {val:<42}".format(val=criado[:42]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.WHITE + "  ⏰ Expiração: {val:<40}".format(val=expira[:40]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.GREEN + "  🔗 Conexões Max: {val:<37}".format(val=safe(userinfo.get('max_connections'))) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.RED + "  📡 Conexões Ativas: {val:<34}".format(val=safe(userinfo.get('active_cons'))) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
        print(Fore.CYAN + "  ║" + Fore.GREEN + "  📺 Canais: {val:<43}".format(val=live) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.BLUE + "  🎬 Filmes: {val:<43}".format(val=vod) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.MAGENTA + "  📺 Séries: {val:<43}".format(val=series) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
        print(Fore.CYAN + "  ║" + Fore.WHITE + "  🌐 Host: {val:<45}".format(val=server[:45]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ║" + Fore.YELLOW + "  🔎 URL: {val:<46}".format(val=safe(url_server)[:46]) + Fore.CYAN + "║")
        print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝")
        print(Fore.CYAN + "\n  📋 M3U Link:")
        print(Fore.WHITE + "  " + m3u_link[:70])
    
    sys.stdout.flush()
    
    # Salva resultado
    salvar_resultado("""
╔══════════════════════════════════════════════════════════════╗
║                    SERVIDOR IPTV ATIVO                       ║
╠══════════════════════════════════════════════════════════════╣
🟢 STATUS: ATIVO
👤 USUÁRIO: {username}
🔑 SENHA: {password}
📅 CRIADO: {criado}
⏰ EXPIRA: {expira}
🔗 CONEXÕES MAX: {max_conn}
📡 CONEXÕES ATIVAS: {active_conn}
📺 CANAIS: {live}
🎬 FILMES: {vod}
📺 SÉRIES: {series}
🌍 TIMEZONE: {timezone}
🕒 HORA ATUAL: {time_now}
🌐 HOST: {server}
🔎 URL: {url_server}
🔗 M3U: {m3u_link}
▬▬▬ஜ۩ IPTV MIGRATOR PRO ۩ஜ▬▬▬
""".format(
        username=username, password=password, criado=criado, expira=expira,
        max_conn=safe(userinfo.get('max_connections')),
        active_conn=safe(userinfo.get('active_cons')),
        live=live, vod=vod, series=series,
        timezone=safe(serverinfo.get('timezone')),
        time_now=safe(serverinfo.get('time_now')),
        server=server, url_server=url_server, m3u_link=m3u_link
    ))
    
    return True

# ══════════════════════════════════════════════════════════════════════════════
# WORKERS E PROCESSAMENTO
# ══════════════════════════════════════════════════════════════════════════════

def worker(lista, user, pwd, show_output=True):
    """Worker para processar lista de servidores."""
    for srv in lista:
        if not running:
            break
        testar_servidor(srv, user, pwd, show_output)

def verificar_dominios_gerados(domains, checker):
    """Verifica lista de domínios gerados."""
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for d in domains:
            future = executor.submit(checker.full_check, d)
            futures[future] = d
        
        for future in as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                if result["dns_resolved"]:
                    print(Fore.YELLOW + "  ◈ DNS OK: {domain} [{ip}]".format(
                        domain=domain, ip=result["ip"]
                    ))
                    
                    if result["http_active"]:
                        print(Fore.GREEN + "    ✓ HTTP Ativo")
                        salvar_dominio_disponivel(domain, result["ip"])
                        
                        if result["iptv_service"]:
                            print(Fore.GREEN + "    ★ SERVIDOR IPTV ENCONTRADO!")
                            salvar_servidor_ativo(domain)
            except Exception as e:
                log_error("Erro verificando {domain}: {err}".format(domain=domain, err=str(e)))
    
    return results

def processar_intercalado(hosts, user, pwd, batch_size=50):
    """
    Processa hosts de forma intercalada:
    - 50 hosts do arquivo
    - 50 domínios gerados (verificados em paralelo)
    """
    global running
    
    generator = DomainGenerator()
    checker = DomainChecker()
    
    total_hosts = len(hosts)
    processed = 0
    
    print(Fore.CYAN + "\n  ╔══════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "          MODO INTERCALADO 50/50 ATIVADO                  " + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝\n")
    
    while processed < total_hosts and running:
        # Lote do arquivo
        batch_end = min(processed + batch_size, total_hosts)
        file_batch = hosts[processed:batch_end]
        
        print(Fore.GREEN + "\n  ▶ Processando lote {start}-{end} do arquivo ({total} restantes)".format(
            start=processed + 1, end=batch_end, total=total_hosts - processed
        ))
        
        # Thread para processar hosts do arquivo
        file_thread = threading.Thread(
            target=worker,
            args=(file_batch, user, pwd, True)
        )
        file_thread.start()
        
        # Gerar e verificar domínios em paralelo
        print(Fore.YELLOW + "  ▶ Gerando e verificando {size} domínios em paralelo...".format(
            size=batch_size
        ))
        
        generated_domains = generator.generate_combinations(limit=batch_size)
        
        if generated_domains:
            # Adiciona ao cache
            for d in generated_domains:
                generator._save_to_cache(d)
            
            # Verifica em paralelo
            verificar_dominios_gerados(generated_domains, checker)
        
        # Aguarda thread de arquivos
        file_thread.join()
        
        processed = batch_end
        print_progress(processed, total_hosts, "Progresso Total")
        print()
    
    return True

def modo_apenas_geracao(quantidade=200):
    """Modo que apenas gera e verifica domínios."""
    generator = DomainGenerator()
    checker = DomainChecker()
    
    print(Fore.CYAN + "\n  ╔══════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "            MODO GERAÇÃO DE DOMÍNIOS                       " + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝\n")
    
    print(Fore.GREEN + "  ▶ Gerando {qty} domínios...".format(qty=quantidade))
    
    domains = generator.generate_combinations(limit=quantidade)
    
    if not domains:
        print(Fore.RED + "  ⚠ Nenhum novo domínio para gerar")
        return
    
    print(Fore.GREEN + "  ✓ {count} domínios gerados".format(count=len(domains)))
    print(Fore.YELLOW + "  ▶ Verificando disponibilidade...\n")
    
    # Salva no cache
    for d in domains:
        generator._save_to_cache(d)
    
    # Verifica todos
    results = verificar_dominios_gerados(domains, checker)
    
    # Estatísticas
    dns_ok = sum(1 for r in results if r["dns_resolved"])
    http_ok = sum(1 for r in results if r["http_active"])
    iptv_ok = sum(1 for r in results if r["iptv_service"])
    
    print(Fore.CYAN + "\n  ╔══════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "                    RESULTADO                              " + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
    print(Fore.CYAN + "  ║" + Fore.WHITE + "  Domínios verificados: {val:<34}".format(val=len(results)) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.GREEN + "  DNS resolvidos: {val:<39}".format(val=dns_ok) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "  HTTP ativos: {val:<42}".format(val=http_ok) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.GREEN + "  Servidores IPTV: {val:<38}".format(val=iptv_ok) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝\n")

# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES PRINCIPAIS
# ══════════════════════════════════════════════════════════════════════════════

def solicitar_credenciais():
    """Solicita credenciais do usuário."""
    print(Fore.CYAN + "\n  ┌─────────────────────────────────────────┐")
    print(Fore.CYAN + "  │" + Fore.YELLOW + "  Digite as credenciais (user:pass)     " + Fore.CYAN + "│")
    print(Fore.CYAN + "  └─────────────────────────────────────────┘")
    
    try:
        cred = input(Fore.GREEN + "  ➤ ").strip()
    except KeyboardInterrupt:
        return None, None
    
    if ":" not in cred:
        print(Fore.RED + "\n  ⚠ Formato inválido! Use: usuario:senha")
        return None, None
    
    user, pwd = cred.split(":", 1)
    return user.strip(), pwd.strip()

def modo_normal(hosts, user, pwd):
    """Executa modo normal (apenas arquivo)."""
    print(Fore.CYAN + "\n  ╔══════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "              MODO NORMAL - ARQUIVO                        " + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝\n")
    
    partes = min(10, len(hosts))
    tamanho = max(1, len(hosts) // partes)
    threads = []
    
    for i in range(partes):
        bloco = hosts[i * tamanho:(i + 1) * tamanho]
        if bloco:
            t = threading.Thread(target=worker, args=(bloco, user, pwd))
            t.start()
            threads.append(t)
    
    resto = hosts[partes * tamanho:]
    if resto:
        t = threading.Thread(target=worker, args=(resto, user, pwd))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()

def exibir_resultado_final():
    """Exibe resultado final da execução."""
    global hits, fails, domains_checked, domains_active
    
    print(Fore.CYAN + "\n\n  ╔══════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "  ║" + Fore.GREEN + "              ✓ MIGRAÇÃO FINALIZADA                        " + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
    print(Fore.CYAN + "  ║" + Fore.GREEN + "  Total HITS: {val:<43}".format(val=hits) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.RED + "  Total FAILS: {val:<42}".format(val=fails) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.YELLOW + "  Domínios verificados: {val:<33}".format(val=domains_checked) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.GREEN + "  Servidores ativos encontrados: {val:<24}".format(val=domains_active) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╠══════════════════════════════════════════════════════════╣")
    print(Fore.CYAN + "  ║" + Fore.WHITE + "  Resultados: {val:<43}".format(val=SAVE_FILE[-43:]) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ║" + Fore.WHITE + "  URLs: {val:<49}".format(val=URLS_FILE[-49:]) + Fore.CYAN + "║")
    print(Fore.CYAN + "  ╚══════════════════════════════════════════════════════════╝\n")
    
    salvar_estatisticas()

def iniciar():
    """Função principal de inicialização."""
    global running, hits, fails, domains_checked, domains_active, primeira_info_salva
    
    # Reset contadores
    hits = 0
    fails = 0
    domains_checked = 0
    domains_active = 0
    primeira_info_salva = False
    running = True
    
    print_banner()
    print_menu()
    
    try:
        opcao = input(Fore.GREEN + "  ➤ Escolha uma opção: ").strip()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n  ⚠ Operação cancelada pelo usuário.")
        return
    
    if opcao == "0":
        print(Fore.CYAN + "\n  Até logo! 👋\n")
        return
    
    elif opcao == "1":
        # Modo Normal
        user, pwd = solicitar_credenciais()
        if not user:
            return
        
        hosts = carregar_hosts()
        if not hosts:
            return
        
        modo_normal(hosts, user, pwd)
        exibir_resultado_final()
    
    elif opcao == "2":
        # Modo Intercalado
        user, pwd = solicitar_credenciais()
        if not user:
            return
        
        hosts = carregar_hosts()
        if not hosts:
            return
        
        processar_intercalado(hosts, user, pwd)
        exibir_resultado_final()
    
    elif opcao == "3":
        # Modo Geração
        print(Fore.CYAN + "\n  Quantos domínios gerar? (padrão: 200)")
        try:
            qty_input = input(Fore.GREEN + "  ➤ ").strip()
            qty = int(qty_input) if qty_input else 200
        except (ValueError, KeyboardInterrupt):
            qty = 200
        
        modo_apenas_geracao(qty)
    
    elif opcao == "4":
        # Estatísticas
        exibir_estatisticas()
        input(Fore.CYAN + "  Pressione ENTER para continuar...")
        iniciar()
    
    elif opcao == "5":
        # Configurações
        print(Fore.YELLOW + "\n  ⚙ Configurações em desenvolvimento...")
        time.sleep(2)
        iniciar()
    
    else:
        print(Fore.RED + "\n  ⚠ Opção inválida!")
        time.sleep(1)
        iniciar()

# ══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        iniciar()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n  ⚠ Programa encerrado pelo usuário.")
        running = False
    except Exception as e:
        log_error("Erro fatal: {err}".format(err=str(e)))
        print(Fore.RED + "\n  ⚠ Erro: {err}".format(err=str(e)))
    finally:
        print(Fore.CYAN + "\n  ▬▬▬ஜ۩ IPTV MIGRATOR PRO ۩ஜ▬▬▬\n")
