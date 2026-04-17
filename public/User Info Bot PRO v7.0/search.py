# ══════════════════════════════════════════════
# 🔍  BUSCA — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Busca em banco local + lookup externo (userbot) para casos não encontrados.
Suporta busca por ID, @username e nome parcial.
"""

from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
from telethon.tl.functions.contacts import ResolveUsernameRequest

from db import carregar_dados, salvar_dados, log, agora_str, ensure_user_shape
from config import DEFAULT_HIDDEN
from profile import obter_perfil_completo, aplicar_atualizacao_campos


def buscar_usuario(query: str, username_only: bool = False) -> list:
    """Busca local. Retorna lista de dicts de usuários (com 'id')."""
    db = carregar_dados()
    q  = query.strip().lstrip('@').lower()
    if not q:
        return []

    results = []
    is_id_query = q.isdigit()

    for uid, dados in db.items():
        if uid.startswith("_"):
            continue
        ensure_user_shape(dados)
        nome = (dados.get("nome_atual", "") or "").lower()
        user = (dados.get("username_atual", "") or "").lstrip('@').lower()

        if is_id_query and uid == q:
            results.append({**dados, "id": uid}); continue
        if username_only:
            if q in user and user:
                results.append({**dados, "id": uid})
            continue
        if q in user or q in nome or q == uid:
            results.append({**dados, "id": uid})

    return results


async def resolver_usuario_externo(user_client, query: str):
    q = query.strip().lstrip('@')
    try:
        if q.isdigit():
            return await user_client.get_entity(int(q))
        try:
            res = await user_client(ResolveUsernameRequest(q))
            if res and res.users:
                return res.users[0]
        except (UsernameNotOccupiedError, UsernameInvalidError):
            return None
        return await user_client.get_entity(q)
    except Exception as e:
        log(f"⚠️ resolver_usuario_externo({query}): {e}")
        return None


async def upsert_usuario_externo(user_client, query: str,
                                  fonte: str = "Lookup") -> tuple:
    """Resolve + insere/atualiza no banco. Retorna (uid, dados, criado, mudancas)."""
    db   = carregar_dados()
    user = await resolver_usuario_externo(user_client, query)
    if not user:
        return None, None, False, []

    uid        = str(user.id)
    nome_atual = (f"{getattr(user,'first_name','') or ''} "
                  f"{getattr(user,'last_name','') or ''}").strip() or "Sem nome"
    user_atual = f"@{user.username}" if getattr(user, 'username', None) else "Nenhum"
    extras     = await obter_perfil_completo(user_client, user.id)

    criado, mudancas = False, []
    if uid not in db:
        db[uid] = {
            "id":                user.id,
            "nome_atual":        nome_atual,
            "username_atual":    user_atual,
            "bio":               extras["bio"],
            "phone":             extras["phone"],
            "fotos":             extras["fotos"],
            "restricoes":        extras["restricoes"],
            "grupos":            [], "grupos_ids": [],
            "fonte":             fonte,
            "primeiro_registro": agora_str(),
            "historico":         [],
            "hidden_info":       dict(DEFAULT_HIDDEN),
            "premium":           {"active": False, "modules": []},
            "custom_combo_limits": {},
        }
        criado = True
        log(f"➕ Upsert externo: {nome_atual} ({uid}) via '{query}'")
    else:
        ensure_user_shape(db[uid])
        mudancas = aplicar_atualizacao_campos(
            db[uid],
            nome=nome_atual, username=user_atual,
            bio=extras["bio"], phone=extras["phone"],
            grupo=fonte,
        )
        db[uid]["fotos"]      = extras["fotos"]
        db[uid]["restricoes"] = extras["restricoes"]

    salvar_dados(db)
    return uid, db[uid], criado, mudancas


async def buscar_com_lookup(user_client, query: str,
                             fonte: str = "Busca direta",
                             username_only: bool = False) -> list:
    """Busca local; se vazia e parecer ID/@username, tenta lookup externo."""
    results = buscar_usuario(query, username_only=username_only)
    if results:
        return results
    q = query.strip().lstrip('@')
    looks_like_id   = q.isdigit()
    looks_like_user = q.isalpha() or any(c == '_' for c in q)
    if looks_like_id or looks_like_user:
        uid, dados, _, _ = await upsert_usuario_externo(user_client, query, fonte)
        if dados:
            return [{**dados, "id": uid}]
    return []
