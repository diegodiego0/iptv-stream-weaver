"""
MIGRADOR IPTV ENHANCED
======================
Versão aprimorada com:
- Módulo itertools para geração de domínios combinados
- Módulo whois para verificação de disponibilidade
- Processamento intercalado: 50 hosts do arquivo + 50 gerados

Autor original: Edivaldo
Modificações: Geração automática de domínios e verificação whois
"""

import requests
import threading
import os
import time
import sys
from datetime import datetime
from colorama import Fore, init

# ======================================================================
# NOVOS IMPORTS - ITERTOOLS E WHOIS
# ======================================================================
import itertools
import socket
import concurrent.futures

# Tentativa de importar whois (python-whois)
try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False
    print(Fore.YELLOW + "⚠️ Módulo whois não instalado. Execute: pip install python-whois")

# Caminhos fixos
HOSTS_FILE = "/sdcard/server/hosts.txt"
SAVE_FILE = "/sdcard/hits/7773H_souiptv_migrado.txt"
URLS_FILE = "/sdcard/hits/novas_urls.txt"
GENERATED_HOSTS_FILE = "/sdcard/server/hosts_gerados.txt"
AVAILABLE_DOMAINS_FILE = "/sdcard/hits/dominios_disponiveis.txt"

hits = 0
fails = 0
generated_count = 0
available_domains = 0
lock = threading.Lock()
primeira_info_salva = False

os.makedirs("/sdcard/hits", exist_ok=True)
os.makedirs("/sdcard/server", exist_ok=True)

# ======================================================================
# CONFIGURAÇÃO DE GERAÇÃO DE DOMÍNIOS (ITERTOOLS)
# ======================================================================

# Prefixos comuns para servidores IPTV
PREFIXES = [
    "tv", "iptv", "stream", "live", "play", "box", "mega", "super",
    "ultra", "hd", "full", "net", "web", "online", "fast", "pro",
    "premium", "gold", "vip", "master", "top", "max", "plus", "best"
]

# Sufixos comuns
SUFFIXES = [
    "tv", "iptv", "stream", "play", "box", "net", "online", "hd",
    "live", "cast", "media", "hub", "zone", "world", "brasil", "br"
]

# Palavras do meio
MIDDLE_WORDS = [
    "", "mega", "super", "ultra", "hd", "full", "pro", "vip", "max",
    "plus", "prime", "gold", "premium", "master", "top", "best"
]

# TLDs para testar
TLDS = [
    ".com", ".net", ".tv", ".me", ".io", ".co", ".org", ".info",
    ".online", ".live", ".stream", ".app", ".xyz", ".club"
]

# Portas comuns de IPTV
COMMON_PORTS = ["", ":80", ":8080", ":8000", ":25461", ":25463", ":8880", ":2095", ":2096"]


# ======================================================================
# CLASSE GERADORA DE DOMÍNIOS (ITERTOOLS)
# ======================================================================
class DomainGenerator:
    """
    Gera combinações de domínios usando itertools.
    Combina prefixos, sufixos, palavras do meio e TLDs.
    """
    
    def __init__(self):
        self.generated_domains = set()
        self.lock = threading.Lock()
    
    def generate_combinations(self, count=50):
        """
        Gera 'count' domínios únicos usando itertools.product e combinations
        """
        domains = []
        
        # Estratégia 1: prefix + suffix + tld
        combo1 = itertools.product(PREFIXES, SUFFIXES, TLDS)
        
        # Estratégia 2: prefix + middle + suffix + tld  
        combo2 = itertools.product(PREFIXES, MIDDLE_WORDS, SUFFIXES, TLDS)
        
        # Estratégia 3: Combinações de 2 prefixos + tld
        combo3 = itertools.product(
            itertools.combinations(PREFIXES, 2), 
            TLDS
        )
        
        # Estratégia 4: prefix + numeros + tld
        numbers = ["", "1", "2", "3", "4", "5", "123", "tv", "hd", "4k"]
        combo4 = itertools.product(PREFIXES, numbers, TLDS)
        
        # Coletar domínios de cada estratégia
        all_combos = []
        
        # Processar combo1
        for prefix, suffix, tld in itertools.islice(combo1, count * 2):
            if prefix != suffix:
                domain = f"{prefix}{suffix}{tld}"
                all_combos.append(domain)
        
        # Processar combo2
        for prefix, middle, suffix, tld in itertools.islice(combo2, count * 2):
            if prefix != suffix and middle:
                domain = f"{prefix}{middle}{suffix}{tld}"
                all_combos.append(domain)
            elif not middle:
                domain = f"{prefix}{suffix}{tld}"
                all_combos.append(domain)
        
        # Processar combo3
        for (p1, p2), tld in itertools.islice(combo3, count):
            domain = f"{p1}{p2}{tld}"
            all_combos.append(domain)
        
        # Processar combo4
        for prefix, num, tld in itertools.islice(combo4, count):
            domain = f"{prefix}{num}{tld}"
            all_combos.append(domain)
        
        # Remover duplicatas e já usados
        with self.lock:
            for domain in all_combos:
                domain_clean = domain.lower().strip()
                if domain_clean not in self.generated_domains:
                    self.generated_domains.add(domain_clean)
                    domains.append(domain_clean)
                    if len(domains) >= count:
                        break
        
        return domains[:count]
    
    def generate_with_ports(self, count=50):
        """
        Gera domínios com portas comuns
        """
        base_domains = self.generate_combinations(count // len(COMMON_PORTS) + 1)
        domains_with_ports = []
        
        for domain in base_domains:
            for port in COMMON_PORTS:
                full_domain = f"{domain}{port}"
                domains_with_ports.append(full_domain)
                if len(domains_with_ports) >= count:
                    return domains_with_ports[:count]
        
        return domains_with_ports[:count]


# ======================================================================
# CLASSE VERIFICADOR DE DOMÍNIOS (WHOIS)
# ======================================================================
class DomainChecker:
    """
    Verifica disponibilidade de domínios usando whois e socket.
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.available = []
        self.unavailable = []
    
    def check_dns(self, domain):
        """
        Verifica se o domínio resolve via DNS (rápido)
        """
        # Remover porta se existir
        clean_domain = domain.split(":")[0] if ":" in domain else domain
        
        try:
            socket.setdefaulttimeout(3)
            ip = socket.gethostbyname(clean_domain)
            return True, ip
        except socket.gaierror:
            return False, None
        except socket.timeout:
            return False, None
        except Exception:
            return False, None
    
    def check_whois(self, domain):
        """
        Verifica registro whois do domínio
        Retorna: (registrado: bool, info: dict ou None)
        """
        if not WHOIS_AVAILABLE:
            return None, None
        
        # Remover porta se existir
        clean_domain = domain.split(":")[0] if ":" in domain else domain
        
        try:
            w = whois.whois(clean_domain)
            if w.domain_name:
                return True, {
                    "domain": w.domain_name,
                    "registrar": w.registrar,
                    "creation_date": str(w.creation_date) if w.creation_date else "N/A",
                    "expiration_date": str(w.expiration_date) if w.expiration_date else "N/A",
                    "name_servers": w.name_servers
                }
            else:
                return False, None
        except whois.parser.PywhoisError:
            return False, None
        except Exception as e:
            return None, None
    
    def check_http_server(self, domain):
        """
        Verifica se há servidor HTTP respondendo (teste de IPTV)
        """
        protocols = ["http://", "https://"]
        
        for proto in protocols:
            try:
                url = f"{proto}{domain}/player_api.php"
                r = requests.get(url, timeout=5, allow_redirects=True)
                if r.status_code == 200:
                    return True, proto
                elif r.status_code in [401, 403]:
                    # Servidor existe mas requer auth
                    return True, proto
            except requests.exceptions.SSLError:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except Exception:
                continue
        
        return False, None
    
    def full_check(self, domain):
        """
        Verificação completa: DNS + WHOIS + HTTP
        Retorna dict com resultados
        """
        result = {
            "domain": domain,
            "dns_resolves": False,
            "ip": None,
            "whois_registered": None,
            "whois_info": None,
            "http_active": False,
            "protocol": None,
            "is_available": False,
            "is_active_iptv": False
        }
        
        # 1. Check DNS
        dns_ok, ip = self.check_dns(domain)
        result["dns_resolves"] = dns_ok
        result["ip"] = ip
        
        # 2. Check WHOIS (se DNS não resolver)
        if not dns_ok:
            whois_reg, whois_info = self.check_whois(domain)
            result["whois_registered"] = whois_reg
            result["whois_info"] = whois_info
            
            # Domínio disponível se não resolver DNS e não estiver registrado
            if whois_reg == False:
                result["is_available"] = True
        
        # 3. Check HTTP (se DNS resolver)
        if dns_ok:
            http_ok, proto = self.check_http_server(domain)
            result["http_active"] = http_ok
            result["protocol"] = proto
            result["is_active_iptv"] = http_ok
        
        return result
    
    def batch_check(self, domains, max_workers=10):
        """
        Verifica múltiplos domínios em paralelo
        """
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {
                executor.submit(self.full_check, domain): domain 
                for domain in domains
            }
            
            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Atualizar listas
                    with self.lock:
                        if result["is_available"]:
                            self.available.append(domain)
                        elif result["is_active_iptv"]:
                            self.unavailable.append(domain)
                except Exception as e:
                    print(Fore.RED + f"Erro ao verificar {domain}: {e}")
        
        return results


# ======================================================================
# SESSION NOVA (SEMPRE LIMPA)
# ======================================================================
def nova_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 10)"
    })
    return s


# ======================================================================
# FUNÇÕES BASE
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


# ======================================================================
# SALVAR DOMÍNIOS GERADOS E DISPONÍVEIS
# ======================================================================
def salvar_dominio_gerado(domain, status_info):
    """
    Salva informações do domínio gerado
    """
    with lock:
        try:
            with open(GENERATED_HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{domain}|{status_info}\n")
                f.flush()
        except Exception as e:
            print(Fore.RED + f"Erro ao salvar domínio gerado: {e}")


def salvar_dominio_disponivel(domain, info):
    """
    Salva domínios disponíveis para registro
    """
    global available_domains
    with lock:
        try:
            with open(AVAILABLE_DOMAINS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🟢 DISPONÍVEL: {domain}\n")
                if info:
                    f.write(f"   Info: {info}\n")
                f.write("─" * 40 + "\n")
                f.flush()
            available_domains += 1
        except Exception as e:
            print(Fore.RED + f"Erro ao salvar domínio disponível: {e}")


def salvar_servidor_iptv_ativo(domain, protocol):
    """
    Salva servidores IPTV ativos encontrados
    """
    with lock:
        try:
            # Adicionar ao hosts.txt para teste posterior
            with open(HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{domain}\n")
            print(Fore.GREEN + f"✅ IPTV ATIVO ENCONTRADO: {domain}")
        except Exception as e:
            print(Fore.RED + f"Erro ao salvar servidor IPTV: {e}")


# ======================================================================
# VALIDA SE DADOS ESTÃO COMPLETOS
# ======================================================================
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


# ======================================================================
# SALVA BLOCO COMPLETO NO ARQUIVO novas_urls.txt (FORMATO LINEAR)
# ======================================================================
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


# ======================================================================
# SALVA URL NUMERADA SEM DUPLICAR
# ======================================================================
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


# ======================================================================
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


# ======================================================================
def carregar_hosts():
    if not os.path.exists(HOSTS_FILE):
        print(Fore.RED + "ERRO: Arquivo hosts não encontrado!")
        return []
    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        hosts = list(dict.fromkeys([h.strip() for h in f if h.strip()]))
    print(Fore.GREEN + f"Servidores carregados: {len(hosts)}")
    return hosts


# ======================================================================
def formatar_data(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"


# ======================================================================
def contar_conteudo(base_url, user, pwd):
    def req(action):
        s = nova_session()
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


# ======================================================================
# TESTE PRINCIPAL
# ======================================================================
def testar_servidor(server, username, password):
    global hits, fails
    server = server.replace("http://", "").replace("https://", "")
    base_url = f"http://{server}/player_api.php"
    auth_url = f"{base_url}?username={username}&password={password}"

    print(Fore.WHITE + f"\n MIGRAÇÃO EM: {Fore.CYAN}{server}\n")
    print(Fore.YELLOW + f" USER/PASS: {Fore.CYAN}{username}:{password}\n")
    print(Fore.GREEN + f" HITS: {hits} " + Fore.RED + f"OFF: {fails}\n")
    print(Fore.MAGENTA + " ▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬    \n")

    s = nova_session()
    try:
        r = s.get(auth_url, timeout=8)
        data = r.json()
    except Exception:
        with lock:
            fails += 1
        return
    finally:
        s.close()

    if "user_info" not in data or data["user_info"].get("auth") != 1:
        with lock:
            fails += 1
        return

    with lock:
        hits += 1

    userinfo = data["user_info"]
    serverinfo = data.get("server_info", {})
    criado = formatar_data(userinfo.get("created_at", 0))
    expira = formatar_data(userinfo.get("exp_date", 0))
    live, vod, series = contar_conteudo(base_url, username, password)
    url_server = serverinfo.get("url", "N/A")
    salvar_novo_host(url_server)

    def safe(v): return str(v) if v is not None else "N/A"
    m3u_link = f"http://{server}/get.php?username={safe(userinfo.get('username'))}&password={safe(userinfo.get('password'))}&type=m3u"

    # 🔥 NOVA LÓGICA PARA novas_urls.txt
    if dados_completos(userinfo, criado, expira):
        salvar_estrutura_completa(
            username, password, criado, expira,
            userinfo, serverinfo, server,
            url_server, live, vod, series, m3u_link
        )
        salvar_url_estrutura(url_server)

    # ----------------- CONSOLE ORIGINAL -----------------
    print(Fore.CYAN + "▬▬▬▬▬ஜ۩ INFORMAÇÕES DO SERVIDOR ۩ஜ▬▬▬▬▬")
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
""")


# ======================================================================
# WORKER PARA HOSTS DO ARQUIVO
# ======================================================================
def worker(lista, user, pwd):
    for srv in lista:
        testar_servidor(srv, user, pwd)


# ======================================================================
# WORKER PARA VERIFICAÇÃO DE DOMÍNIOS GERADOS (WHOIS + DNS)
# ======================================================================
def worker_domain_checker(domains, checker):
    """
    Thread worker para verificar domínios gerados em paralelo
    """
    global generated_count
    
    results = checker.batch_check(domains, max_workers=5)
    
    for result in results:
        domain = result["domain"]
        
        with lock:
            generated_count += 1
        
        if result["is_available"]:
            # Domínio disponível para registro
            print(Fore.GREEN + f"🟢 DISPONÍVEL: {domain}")
            salvar_dominio_disponivel(domain, "Não registrado")
            salvar_dominio_gerado(domain, "DISPONÍVEL")
            
        elif result["is_active_iptv"]:
            # Servidor IPTV ativo encontrado!
            print(Fore.CYAN + f"📺 IPTV ATIVO: {domain}")
            salvar_servidor_iptv_ativo(domain, result["protocol"])
            salvar_dominio_gerado(domain, f"IPTV_ATIVO|{result['protocol']}")
            
        elif result["dns_resolves"]:
            # Domínio existe mas não é IPTV
            print(Fore.YELLOW + f"⚠️ EXISTE (não IPTV): {domain} -> {result['ip']}")
            salvar_dominio_gerado(domain, f"EXISTE|{result['ip']}")
            
        else:
            # Verificação inconclusiva
            print(Fore.WHITE + f"❓ VERIFICANDO: {domain}")
            salvar_dominio_gerado(domain, "VERIFICADO")


# ======================================================================
# PROCESSADOR INTERCALADO (50 ARQUIVO + 50 GERADOS)
# ======================================================================
def processar_intercalado(hosts, user, pwd, batch_size=50):
    """
    Processa hosts em lotes intercalados:
    - 50 hosts do arquivo hosts.txt
    - 50 domínios gerados pelo itertools (verificados via whois)
    
    Execução paralela: enquanto 50 do arquivo processam,
    os 50 gerados são verificados simultaneamente.
    """
    global generated_count
    
    generator = DomainGenerator()
    checker = DomainChecker()
    
    total_hosts = len(hosts)
    processed = 0
    batch_num = 0
    
    print(Fore.CYAN + "\n" + "=" * 60)
    print(Fore.CYAN + "🔄 MODO INTERCALADO ATIVADO")
    print(Fore.CYAN + f"📁 {total_hosts} hosts do arquivo")
    print(Fore.CYAN + f"🔢 Lotes de {batch_size} hosts + {batch_size} gerados")
    print(Fore.CYAN + "=" * 60 + "\n")
    
    while processed < total_hosts:
        batch_num += 1
        
        # Pegar próximo lote de hosts do arquivo
        batch_hosts = hosts[processed:processed + batch_size]
        
        # Gerar domínios para verificar em paralelo
        generated_domains = generator.generate_with_ports(batch_size)
        
        print(Fore.MAGENTA + f"\n{'='*60}")
        print(Fore.MAGENTA + f"📦 LOTE {batch_num}")
        print(Fore.MAGENTA + f"   📁 Hosts do arquivo: {len(batch_hosts)}")
        print(Fore.MAGENTA + f"   🔧 Domínios gerados: {len(generated_domains)}")
        print(Fore.MAGENTA + f"{'='*60}\n")
        
        # Criar threads para processamento paralelo
        threads = []
        
        # Thread 1: Processar hosts do arquivo (dividir em sub-threads)
        partes = min(10, len(batch_hosts))
        if partes > 0:
            tamanho = max(1, len(batch_hosts) // partes)
            for i in range(partes):
                bloco = batch_hosts[i * tamanho:(i + 1) * tamanho]
                if bloco:
                    t = threading.Thread(target=worker, args=(bloco, user, pwd))
                    t.start()
                    threads.append(t)
            
            # Resto
            resto = batch_hosts[partes * tamanho:]
            if resto:
                t = threading.Thread(target=worker, args=(resto, user, pwd))
                t.start()
                threads.append(t)
        
        # Thread 2: Verificar domínios gerados via whois/dns
        if generated_domains:
            t_checker = threading.Thread(
                target=worker_domain_checker,
                args=(generated_domains, checker)
            )
            t_checker.start()
            threads.append(t_checker)
        
        # Aguardar todas as threads do lote
        for t in threads:
            t.join()
        
        processed += len(batch_hosts)
        
        # Status do lote
        print(Fore.GREEN + f"\n✅ LOTE {batch_num} CONCLUÍDO")
        print(Fore.GREEN + f"   Processados: {processed}/{total_hosts}")
        print(Fore.GREEN + f"   Gerados verificados: {generated_count}")
        print(Fore.GREEN + f"   Domínios disponíveis: {available_domains}")
        print(Fore.GREEN + f"   HITS: {hits} | OFF: {fails}")
    
    return checker


# ======================================================================
# INICIAR
# ======================================================================
def iniciar():
    global hits, fails, generated_count, available_domains
    
    try:
        os.system("clear")
    except Exception:
        pass
    
    init(autoreset=True)  # Inicializar colorama
    
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "   MIGRADOR IPTV ENHANCED")
    print(Fore.CYAN + "   com itertools + whois")
    print(Fore.CYAN + "=" * 60)
    print()
    
    # Verificar dependências
    if not WHOIS_AVAILABLE:
        print(Fore.YELLOW + "⚠️ Módulo whois não disponível.")
        print(Fore.YELLOW + "   Instale com: pip install python-whois")
        print(Fore.YELLOW + "   Continuando apenas com verificação DNS/HTTP...")
        print()
    
    print(Fore.CYAN + "Digite user:pass")
    cred = input("➤ ").strip()
    if ":" not in cred:
        print(Fore.RED + "Formato inválido.")
        return
    
    user, pwd = cred.split(":", 1)
    
    hosts = carregar_hosts()
    if not hosts:
        return
    
    print(Fore.CYAN + "\nEscolha o modo de processamento:")
    print(Fore.WHITE + "1. Normal (apenas hosts do arquivo)")
    print(Fore.GREEN + "2. Intercalado (50 arquivo + 50 gerados)")
    print(Fore.YELLOW + "3. Apenas gerar e verificar domínios")
    
    modo = input("\n➤ Modo (1/2/3): ").strip()
    
    if modo == "2":
        # Modo intercalado
        print(Fore.CYAN + "\nQuantos hosts por lote? (padrão: 50)")
        try:
            batch_size = int(input("➤ ").strip() or "50")
        except:
            batch_size = 50
        
        checker = processar_intercalado(hosts, user, pwd, batch_size)
        
    elif modo == "3":
        # Apenas gerar domínios
        print(Fore.CYAN + "\nQuantos domínios gerar?")
        try:
            qtd = int(input("➤ ").strip() or "100")
        except:
            qtd = 100
        
        generator = DomainGenerator()
        checker = DomainChecker()
        
        print(Fore.CYAN + f"\n🔧 Gerando {qtd} domínios...")
        domains = generator.generate_with_ports(qtd)
        
        print(Fore.CYAN + f"🔍 Verificando {len(domains)} domínios...")
        worker_domain_checker(domains, checker)
        
    else:
        # Modo normal (original)
        partes = 10
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
    
    # Resumo final
    print(Fore.GREEN + "\n" + "=" * 60)
    print(Fore.GREEN + "🏁 MIGRAÇÃO FINALIZADA!")
    print(Fore.GREEN + "=" * 60)
    print(Fore.YELLOW + f"📊 TOTAL HITS: {hits}")
    print(Fore.RED + f"📊 TOTAL OFF: {fails}")
    print(Fore.CYAN + f"🔧 DOMÍNIOS GERADOS: {generated_count}")
    print(Fore.GREEN + f"🟢 DOMÍNIOS DISPONÍVEIS: {available_domains}")
    print()
    print(Fore.CYAN + f"📁 Resultados: {SAVE_FILE}")
    print(Fore.CYAN + f"📁 URLs: {URLS_FILE}")
    print(Fore.CYAN + f"📁 Gerados: {GENERATED_HOSTS_FILE}")
    print(Fore.CYAN + f"📁 Disponíveis: {AVAILABLE_DOMAINS_FILE}")


if __name__ == "__main__":
    iniciar()
