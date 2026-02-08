#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
▬▬▬ஜ۩ 9Xtream Migrador v2 - Com IterTools ۩ஜ▬▬▬
Gera variações de servidores automaticamente a partir de hits.
"""

import requests
import threading
import os
import time
import sys
import re
import itertools
import random
import string
from datetime import datetime
from collections import defaultdict

try:
    from colorama import Fore, init
    init(autoreset=True)
except ImportError:
    # Fallback se colorama não estiver instalado
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = RESET = ""

# ======================================================================
# CONFIGURAÇÕES
# ======================================================================

HOSTS_FILE = "/sdcard/server/hosts.txt"
SAVE_FILE = "/sdcard/hits/7773H_souiptv5_migrado.txt"
URLS_FILE = "/sdcard/hits/novas_urls5.txt"
GENERATED_HOSTS_FILE = "/sdcard/server/hosts_gerados5.txt"
MAX_THREADS = 10
TIMEOUT_AUTH = 8
TIMEOUT_CONTENT = 7
MAX_RETRIES = 2
RETRY_DELAY = 1

# Controle de variações do itertools
ITERTOOLS_CONFIG = {
    "max_variações_por_hit": 50,      # máximo de variações por servidor hit
    "range_numerico": 20,              # ex: v166 → testa v146..v186
    "portas_comuns": [80, 443, 8080, 8000, 8880, 25461, 2082, 2083, 2086, 2095],
    "subdomínios_comuns": ["ad", "cdn", "tv", "iptv", "stream", "live", "panel", "dns", "srv", "play"],
    "testar_gerados": True,            # testar variações automaticamente
}

# ======================================================================
# ESTADO GLOBAL
# ======================================================================

hits = 0
fails = 0
total_gerados = 0
total_gerados_hits = 0
lock = threading.Lock()
primeira_info_salva = False
hosts_testados = set()  # evita testar o mesmo host 2x
hosts_testados_lock = threading.Lock()

os.makedirs("/sdcard/hits", exist_ok=True)
os.makedirs("/sdcard/server", exist_ok=True)

# ======================================================================
# SESSION COM RETRY
# ======================================================================

def nova_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 10)"
    })
    a = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[500, 502, 503, 504],
        ),
        pool_connections=5,
        pool_maxsize=10,
    )
    s.mount("http://", a)
    s.mount("https://", a)
    return s

# ======================================================================
# FUNÇÕES DE ARQUIVO (THREAD-SAFE)
# ======================================================================

def salvar_resultado(texto):
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
        print(Fore.RED + f"Erro ao salvar resultado: {e}")

def dados_completos(userinfo, criado, expira):
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
    global primeira_info_salva
    if primeira_info_salva:
        return
    with lock:
        if primeira_info_salva:
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
            primeira_info_salva = True
        except Exception as e:
            print(Fore.RED + f"Erro ao salvar estrutura completa: {e}")

def salvar_url_estrutura(url_server):
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
        num = sum(1 for l in linhas if l.startswith("🔎URL")) + 1
        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔎URL {num}: {url_server}\n")
                f.flush()
        except Exception:
            pass

def salvar_novo_host(url_server):
    if not url_server or url_server == "N/A":
        return
    url_server = url_server.strip().lower()
    base = url_server.split(":", 1)[0] if ":" in url_server else url_server
    with lock:
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

def salvar_host_gerado(host):
    """Salva hosts gerados pelo itertools em arquivo separado."""
    with lock:
        try:
            with open(GENERATED_HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(host + "\n")
        except Exception:
            pass

# ======================================================================
# 🔥 ITERTOOLS - GERADOR DE VARIAÇÕES DE SERVIDORES
# ======================================================================

def extrair_componentes(server):
    """
    Extrai componentes de um servidor para gerar variações.
    Ex: "ad.v166.xyz:80" → subdomínio="ad", parte_num="v166", domínio="xyz", porta=80
    """
    server_clean = server.replace("http://", "").replace("https://", "").strip().lower()

    # Separar host e porta
    if ":" in server_clean:
        host_part, porta_str = server_clean.rsplit(":", 1)
        try:
            porta = int(porta_str)
            tem_porta = True
        except ValueError:
            host_part = server_clean
            porta = None
            tem_porta = False
    else:
        host_part = server_clean
        porta = None
        tem_porta = False

    partes = host_part.split(".")

    return {
        "original": server_clean,
        "host": host_part,
        "partes": partes,
        "porta": porta,
        "tem_porta": tem_porta,
        "num_partes": len(partes),
    }

def encontrar_numeros(texto):
    """Encontra todos os números dentro de um texto."""
    return [(m.start(), m.end(), int(m.group())) for m in re.finditer(r'\d+', texto)]

def _normalizar_host(host_str):
    """
    Normaliza um host para comparação anti-duplicata:
    - lowercase
    - Remove porta padrão 80 se presente
    Retorna string normalizada.
    """
    h = host_str.strip().lower()
    # Remover porta 80 padrão para comparação
    if h.endswith(":80"):
        h = h[:-3]
    return h

def gerar_variacoes_servidor(server):
    """
    🔥 CORE DO ITERTOOLS
    Gera variações inteligentes de um servidor que deu hit.

    Estratégias:
    1. Variação numérica: v166 → v146..v186 (SEM alterar porta)
    2. Variação de porta: SOMENTE se o host original NÃO tem porta
    3. Variação de subdomínio: ad.v166 → cdn.v166, tv.v166, etc. (preserva porta original)
    4. Variação combinada: muda número (SEM alterar porta)
    5. Variação de letras em prefixos: ad → ae, af, bd, cd, etc. (preserva porta original)

    CORREÇÕES APLICADAS:
    - Todas as variações são normalizadas para lowercase (sem duplicatas por case)
    - Não adiciona porta a hosts que já possuem porta
    - Variações numéricas preservam a porta original intacta
    """
    comp = extrair_componentes(server)
    variacoes_normalizadas = set()  # set de hosts normalizados para dedup
    variacoes_resultado = []         # lista final sem duplicatas

    host = comp["host"]
    porta_original = comp["porta"]
    tem_porta = comp["tem_porta"]
    partes = comp["partes"]
    cfg = ITERTOOLS_CONFIG

    def _sufixo_porta():
        """Retorna sufixo de porta apenas se o original tinha porta."""
        if tem_porta and porta_original is not None:
            return ":{port}".format(port=porta_original)
        return ""

    def _adicionar_variacao(novo_host_completo):
        """
        Adiciona variação ao set, evitando duplicatas case-insensitive
        e evitando duplicatas com/sem porta padrão.
        """
        normalizado = _normalizar_host(novo_host_completo)
        if normalizado not in variacoes_normalizadas:
            variacoes_normalizadas.add(normalizado)
            # Salva em lowercase para consistência
            variacoes_resultado.append(novo_host_completo.lower())

    # ------------------------------------------------------------------
    # 1. VARIAÇÃO NUMÉRICA - muda números encontrados no host
    #    Preserva a porta original se existir, NÃO adiciona porta nova
    # ------------------------------------------------------------------
    numeros = encontrar_numeros(host)
    for start, end, num_val in numeros:
        prefixo = host[:start]
        sufixo = host[end:]
        rng = cfg["range_numerico"]
        for delta in range(-rng, rng + 1):
            if delta == 0:
                continue
            novo_num = num_val + delta
            if novo_num < 0:
                continue
            # Manter padding de zeros se o original tiver (ex: 066 → 046)
            original_str = host[start:end]
            novo_str = str(novo_num).zfill(len(original_str))
            novo_host = "{prefixo}{novo_str}{sufixo}".format(
                prefixo=prefixo, novo_str=novo_str, sufixo=sufixo
            )
            _adicionar_variacao("{host}{porta}".format(host=novo_host, porta=_sufixo_porta()))

    # ------------------------------------------------------------------
    # 2. VARIAÇÃO DE PORTA - SOMENTE se o host original NÃO tem porta
    # ------------------------------------------------------------------
    if not tem_porta:
        for porta in cfg["portas_comuns"]:
            _adicionar_variacao("{host}:{porta}".format(host=host, porta=porta))

    # ------------------------------------------------------------------
    # 3. VARIAÇÃO DE SUBDOMÍNIO (primeira parte do host)
    #    Preserva porta original
    # ------------------------------------------------------------------
    if len(partes) >= 3:
        sub_original = partes[0]
        resto = ".".join(partes[1:])
        for sub in cfg["subdomínios_comuns"]:
            if sub.lower() != sub_original.lower():
                _adicionar_variacao("{sub}.{resto}{porta}".format(
                    sub=sub, resto=resto, porta=_sufixo_porta()
                ))

    # ------------------------------------------------------------------
    # 4. VARIAÇÃO DE LETRAS no prefixo (2 chars)
    #    Preserva porta original
    # ------------------------------------------------------------------
    if len(partes) >= 2 and len(partes[0]) == 2 and partes[0].isalpha():
        letras = partes[0]
        resto = ".".join(partes[1:])
        # Variar cada letra individualmente
        for i, char in enumerate(letras):
            for c in string.ascii_lowercase:
                if c != char.lower():
                    nova = list(letras.lower())
                    nova[i] = c
                    novo_sub = "".join(nova)
                    _adicionar_variacao("{sub}.{resto}{porta}".format(
                        sub=novo_sub, resto=resto, porta=_sufixo_porta()
                    ))

    # ------------------------------------------------------------------
    # 5. VARIAÇÃO COMBINADA (número apenas, SEM mudar porta)
    #    Gera variações numéricas com a mesma porta original
    # ------------------------------------------------------------------
    if numeros:
        start, end, num_val = numeros[0]  # primeiro número encontrado
        prefixo = host[:start]
        sufixo = host[end:]
        original_str = host[start:end]
        for delta in [-5, -1, 1, 5, 10]:
            novo_num = num_val + delta
            if novo_num < 0:
                continue
            novo_str = str(novo_num).zfill(len(original_str))
            novo_host = "{prefixo}{novo_str}{sufixo}".format(
                prefixo=prefixo, novo_str=novo_str, sufixo=sufixo
            )
            _adicionar_variacao("{host}{porta}".format(host=novo_host, porta=_sufixo_porta()))

    # Remover o servidor original das variações
    original_normalizado = _normalizar_host(comp["original"])
    variacoes_resultado = [v for v in variacoes_resultado if _normalizar_host(v) != original_normalizado]

    # Limitar quantidade
    variacoes_resultado = variacoes_resultado[:cfg["max_variações_por_hit"]]

    return variacoes_resultado

def ja_testado(server):
    """Verifica se um servidor já foi testado (thread-safe, case-insensitive)."""
    server_clean = _normalizar_host(
        server.replace("http://", "").replace("https://", "")
    )
    with hosts_testados_lock:
        if server_clean in hosts_testados:
            return True
        hosts_testados.add(server_clean)
        return False

# ======================================================================
# FUNÇÕES AUXILIARES
# ======================================================================

def carregar_hosts():
    if not os.path.exists(HOSTS_FILE):
        print(Fore.RED + "ERRO: Arquivo hosts não encontrado!")
        return []
    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        # Dedup case-insensitive ao carregar
        seen = set()
        hosts = []
        for h in f:
            h = h.strip()
            if not h:
                continue
            normalizado = _normalizar_host(h)
            if normalizado not in seen:
                seen.add(normalizado)
                hosts.append(h)
    print(Fore.GREEN + f"Servidores carregados: {len(hosts)}")
    return hosts

def formatar_data(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

def contar_conteudo(base_url, user, pwd):
    def req(action):
        s = nova_session()
        try:
            r = s.get(
                f"{base_url}?username={user}&password={pwd}&action={action}",
                timeout=TIMEOUT_CONTENT
            )
            return len(r.json())
        except Exception:
            return 0
        finally:
            s.close()
    return req("get_live_streams"), req("get_vod_streams"), req("get_series")

# ======================================================================
# TESTE PRINCIPAL
# ======================================================================

def testar_servidor(server, username, password, is_gerado=False):
    global hits, fails, total_gerados_hits

    if ja_testado(server):
        return False

    server = server.replace("http://", "").replace("https://", "")
    base_url = f"http://{server}/player_api.php"
    auth_url = f"{base_url}?username={username}&password={password}"

    tag = Fore.MAGENTA + "[ITERTOOLS] " if is_gerado else ""
    print(Fore.WHITE + f"\n {tag}MIGRAÇÃO EM: {Fore.CYAN}{server}")
    print(Fore.YELLOW + f" USER/PASS: {Fore.CYAN}{username}:{password}")
    print(Fore.GREEN + f" HITS: {hits} " + Fore.RED + f"OFF: {fails}" +
          (Fore.MAGENTA + f" GERADOS-HIT: {total_gerados_hits}" if total_gerados_hits else ""))
    print(Fore.MAGENTA + " ▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬\n")

    s = nova_session()
    try:
        r = s.get(auth_url, timeout=TIMEOUT_AUTH)
        data = r.json()
    except requests.exceptions.Timeout:
        with lock:
            fails += 1
        print(Fore.RED + f" ⏰ Timeout: {server}")
        return False
    except requests.exceptions.ConnectionError:
        with lock:
            fails += 1
        return False
    except Exception:
        with lock:
            fails += 1
        return False
    finally:
        s.close()

    if "user_info" not in data or data["user_info"].get("auth") != 1:
        with lock:
            fails += 1
        return False

    # 🟢 HIT!
    with lock:
        hits += 1
        if is_gerado:
            total_gerados_hits += 1

    userinfo = data["user_info"]
    serverinfo = data.get("server_info", {})

    criado = formatar_data(userinfo.get("created_at", 0))
    expira = formatar_data(userinfo.get("exp_date", 0))

    live, vod, series = contar_conteudo(base_url, username, password)
    url_server = serverinfo.get("url", "N/A")

    salvar_novo_host(url_server)
    if is_gerado:
        salvar_novo_host(server)
        salvar_host_gerado(server)

    def safe(v): return str(v) if v is not None else "N/A"

    m3u_link = (f"http://{server}/get.php?"
                f"username={safe(userinfo.get('username'))}"
                f"&password={safe(userinfo.get('password'))}&type=m3u")

    if dados_completos(userinfo, criado, expira):
        salvar_estrutura_completa(
            username, password, criado, expira,
            userinfo, serverinfo, server,
            url_server, live, vod, series, m3u_link
        )
        salvar_url_estrutura(url_server)

    # Console bonito
    origem = "🧬 ITERTOOLS" if is_gerado else "📋 ORIGINAL"
    print(Fore.CYAN + f"▬▬▬▬▬ஜ۩ {origem} - INFORMAÇÕES DO SERVIDOR ۩ஜ▬▬▬▬▬")
    print(Fore.GREEN + f"🟢 Status: {safe(userinfo.get('status')).upper()}")
    print(Fore.WHITE + "┌─────────────────────────────────────────────┐")
    print(Fore.YELLOW + f"│ 👤 Usuário: {safe(userinfo.get('username')):<27} │")
    print(Fore.YELLOW + f"│ 🔑 Senha: {safe(userinfo.get('password')):<29} │")
    print(Fore.CYAN + f"│ 📅 Criação: {criado:<25} │")
    print(Fore.CYAN + f"│ ⏰ Expiração: {expira:<23} │")
    print(Fore.GREEN + f"│ 🔗 Conexões Max: {safe(userinfo.get('max_connections')):<19} │")
    print(Fore.RED + f"│ 📡 Conexões Ativas: {safe(userinfo.get('active_cons')):<15} │")
    print(Fore.WHITE + "├─────────────────────────────────────────────┤")
    print(Fore.MAGENTA + f"│ 🌐 Host: {server:<31} │")
    print(Fore.YELLOW + f"│ 🔎 URL: {safe(url_server):<32} │")
    print(Fore.BLUE + f"│ 🌍 Timezone: {safe(serverinfo.get('timezone')):<25} │")
    print(Fore.BLUE + f"│ 🕒 Hora Atual: {safe(serverinfo.get('time_now')):<23} │")
    print(Fore.CYAN + f"│ 🔒 Porta HTTPS: {safe(serverinfo.get('https_port')):<21} │")
    print(Fore.CYAN + f"│ 📺 Porta RTMP: {safe(serverinfo.get('rtmp_port')):<22} │")
    print(Fore.GREEN + f"│ 🎯 Protocolo: {safe(serverinfo.get('server_protocol')):<23} │")
    print(Fore.YELLOW + f"│ 🎬 Formato: {safe(serverinfo.get('allowed_output_formats')):<27} │")
    print(Fore.WHITE + "├─────────────────────────────────────────────┤")
    print(Fore.GREEN + f"│ 📺 Canais ao Vivo: {live:<19} │")
    print(Fore.BLUE + f"│ 🎬 Filmes (VOD): {vod:<21} │")
    print(Fore.MAGENTA + f"│ 📺 Séries: {series:<27} │")
    print(Fore.WHITE + "└─────────────────────────────────────────────┘")
    print(Fore.CYAN + "\n📋 LINK M3U:")
    print(Fore.WHITE + f"🔗 {m3u_link}")
    sys.stdout.flush()

    salvar_resultado(f"""
🟢STATUS: ATIVO ({origem})
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
""")
    return True  # foi um hit

# ======================================================================
# WORKER COM ITERTOOLS INTEGRADO
# ======================================================================

def worker(lista, user, pwd):
    global total_gerados
    for srv in lista:
        foi_hit = testar_servidor(srv, user, pwd, is_gerado=False)

        # 🔥 Se deu HIT, ativa o itertools para gerar variações
        if foi_hit and ITERTOOLS_CONFIG["testar_gerados"]:
            variacoes = gerar_variacoes_servidor(srv)
            with lock:
                total_gerados += len(variacoes)
            print(Fore.MAGENTA + f"\n 🧬 ITERTOOLS: Gerou {len(variacoes)} variações de {srv}")
            print(Fore.MAGENTA + f" 🧬 Total gerados até agora: {total_gerados}\n")
            for var_srv in variacoes:
                testar_servidor(var_srv, user, pwd, is_gerado=True)

# ======================================================================
# WORKER PARA HOSTS GERADOS (SEGUNDA RODADA)
# ======================================================================

def worker_gerados(lista, user, pwd):
    for srv in lista:
        testar_servidor(srv, user, pwd, is_gerado=True)

# ======================================================================
# INICIAR
# ======================================================================

def iniciar():
    global total_gerados, total_gerados_hits

    try:
        os.system("clear")
    except Exception:
        pass

    print(Fore.CYAN + "=" * 50)
    print(Fore.MAGENTA + "  ▬▬▬ஜ۩ 9Xtream Migrador v2 ۩ஜ▬▬▬")
    print(Fore.YELLOW + "  🧬 Com IterTools - Gerador de Variações")
    print(Fore.CYAN + "=" * 50)
    print()

    print(Fore.CYAN + "Digite user:pass")
    cred = input("➤ ").strip()
    if ":" not in cred:
        print(Fore.RED + "Formato inválido. Use user:pass")
        return
    user, pwd = cred.split(":", 1)

    hosts = carregar_hosts()
    if not hosts:
        return

    # Registrar hosts originais como já conhecidos (normalizado)
    for h in hosts:
        normalizado = _normalizar_host(
            h.replace("http://", "").replace("https://", "")
        )
        hosts_testados.add(normalizado)

    # Mas limpar para permitir teste
    hosts_testados.clear()

    print(Fore.YELLOW + f"\n🚀 Iniciando migração com {len(hosts)} servidores...")
    print(Fore.MAGENTA + f"🧬 IterTools ativo: variações serão geradas a cada HIT\n")

    inicio = time.time()

    # Fase 1: Testar hosts originais
    partes = MAX_THREADS
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

    duracao = time.time() - inicio

    # Resumo final
    print(Fore.CYAN + "\n" + "=" * 50)
    print(Fore.GREEN + "  ✅ MIGRAÇÃO FINALIZADA!")
    print(Fore.CYAN + "=" * 50)
    print(Fore.GREEN + f"  📊 HITS originais + gerados: {hits}")
    print(Fore.MAGENTA + f"  🧬 Variações geradas: {total_gerados}")
    print(Fore.MAGENTA + f"  🧬 Hits de variações: {total_gerados_hits}")
    print(Fore.RED + f"  ❌ Total OFF: {fails}")
    print(Fore.YELLOW + f"  ⏱️  Tempo: {duracao:.1f}s")
    print(Fore.CYAN + f"  📁 Resultados: {SAVE_FILE}")
    print(Fore.CYAN + f"  📁 Estrutura: {URLS_FILE}")
    print(Fore.CYAN + f"  📁 Hosts gerados: {GENERATED_HOSTS_FILE}")
    print(Fore.MAGENTA + "\n  ▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬\n")

if __name__ == "__main__":
    iniciar()
