# 🕵️ User Info Bot PRO v7.0 — Edição Modular

Bot Telethon profissional para monitoramento de usuários Telegram, busca por
ID/username/nome, geração de combos Xtream Codes a partir dos grupos do usuário,
sistema de idiomas dinâmico (PT-BR/EN/ES) e quotas diárias.

## 📁 Estrutura modular

Todos os arquivos `.py` ficam na MESMA pasta:

| Arquivo        | Responsabilidade |
|----------------|------------------|
| `config.py`    | Credenciais, paths, constantes, padrões regex |
| `db.py`        | Persistência do `user_database.json` |
| `access.py`    | Owner / premium / módulos / limites |
| `lang.py`      | i18n com `lang.json` (mesma pasta) |
| `profile.py`   | Captura/atualização/formatação de perfil |
| `search.py`    | Busca local + lookup externo via userbot |
| `quota.py`     | Controle diário de uso de combos por usuário |
| `combo.py`     | Geração de combos a partir dos grupos do usuário |
| `notifier.py`  | Envia perfil COMPLETO ao owner em qualquer mudança |
| `scan.py`      | Varredura periódica de grupos |
| `dm.py`        | Cadastro/atualização de usuários via DM |
| `ui.py`        | Botões inline e menus |
| `handlers.py`  | Comandos `/start /buscar /lang /setcombo` + callbacks + inline |
| `main.py`      | Inicializa clients e roda o loop |
| `lang.json`    | Traduções (auto-gerado se ausente) |
| `data/`        | Banco e logs (auto-gerado) |

## ▶️ Executar

```bash
pip install telethon
python main.py
```

## 🔍 Como buscar

**Apenas em DM** ou via inline (somente username):

- `/buscar 123456789` — por ID
- `/buscar @username` — por username
- `/buscar Nome` — por nome parcial
- `@InforUser_Bot @username` — inline (somente username)

> Buscas inline por **ID** ou **nome** foram removidas para evitar conflito
> com o próprio `@username` do bot.

## 📋 Combo Xtream

Combos `usuario:senha` extraídos dos grupos onde o **usuário** está.
Sem duplicatas. Quotas diárias:

| Plano   | Limite diário | Distribuição |
|---------|---------------|--------------|
| Free    | **300**       | Apenas dos grupos do usuário |
| Premium | **800 + 200** | 800 dos próprios grupos + 200 de outros = 1000. Se grupos próprios não atingirem 800, completa-se com outros até 1000. |

Owner pode ajustar limites globais ou por usuário:

```
/setcombo global 300 1000
/setcombo @username 500 1500
/setcombo 123456789 500 1500
```

## 🔔 Notificações

Quando QUALQUER campo de um perfil monitorado muda (nome, username, bio,
telefone), o bot envia ao owner:

1. Lista do que mudou (de → para)
2. **Perfil COMPLETO** atualizado do usuário alvo
3. Botão de acesso direto ao perfil no Telegram

## 👨‍💻 Créditos

Edivaldo Silva — `@Edkd1`
