# ══════════════════════════════════════════════
# 🚀  MAIN — User Info Bot PRO v7.0 (modular)
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Orquestra: cria os clientes Telethon (userbot + bot), registra handlers
e mantém o loop ativo.

Estrutura modular (todos os arquivos na MESMA pasta):
  - config.py     credenciais e constantes
  - db.py         persistência json
  - access.py     owner/premium/módulos
  - lang.py       i18n + lang.json
  - profile.py    captura/format do perfil
  - search.py     busca local + lookup externo
  - quota.py     quota diária de combos
  - combo.py      geração de combos por grupos do usuário
  - notifier.py   notificações com perfil completo
  - scan.py       varredura periódica
  - dm.py         salvar/atualizar usuário em DM
  - ui.py         botões inline / menus
  - handlers.py   comandos + callbacks + inline + texto
  - main.py       este arquivo
"""

import asyncio
from telethon import TelegramClient

from config import (API_ID, API_HASH, PHONE, BOT_TOKEN,
                    SESSION_USER, SESSION_BOT, SCAN_INTERVAL)
from db import log
from handlers import register_handlers
import scan as scan_mod


user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot         = TelegramClient(SESSION_BOT,  API_ID, API_HASH)


async def _periodic_scan():
    """Loop em background — varredura a cada SCAN_INTERVAL segundos."""
    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL)
            if not scan_mod.is_scan_running():
                await scan_mod.executar_varredura(user_client, bot)
        except Exception as e:
            log(f"⚠️ periodic_scan: {e}")


async def main():
    log("🚀 Iniciando User Info Bot PRO v7.0 (modular)")
    await user_client.start(phone=PHONE)
    await bot.start(bot_token=BOT_TOKEN)
    register_handlers(bot, user_client)

    asyncio.create_task(_periodic_scan())
    log("✅ Bot online. Aguardando eventos.")
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot.run_until_disconnected(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("🛑 Encerrado pelo usuário.")
