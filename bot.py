"""
Shodan Telegram Bot — Local development entry point (polling mode).
For Azure Functions deployment, use function_app.py instead.

Usage:
    python bot.py          → Run in polling mode (local dev)
    python bot.py --setup  → Set webhook URL (for Azure Functions)
    python bot.py --remove → Remove webhook (switch back to polling)
"""

import sys
import asyncio
import logging

from telegram import Update

from config import TELEGRAM_BOT_TOKEN, SHODAN_API_KEY, LOG_LEVEL
from bot_app import build_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)


async def setup_webhook(url: str):
    """Register webhook with Telegram."""
    from telegram import BotCommand

    app = build_application()
    async with app:
        result = await app.bot.set_webhook(
            url=url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        # Set bot commands
        commands = [
            BotCommand("start", "Mulai bot & tampilkan menu"),
            BotCommand("templates", "Template pencarian siap pakai"),
            BotCommand("t", "Shortcut untuk /templates"),
            BotCommand("search", "Pencarian Shodan langsung"),
            BotCommand("count", "Hitung hasil (hemat credits)"),
            BotCommand("host", "Lookup detail IP"),
            BotCommand("dns", "DNS resolve hostname"),
            BotCommand("rdns", "Reverse DNS lookup"),
            BotCommand("domain", "Info DNS domain"),
            BotCommand("exploit", "Cari exploit"),
            BotCommand("honeypot", "Cek honeypot score"),
            BotCommand("scan", "Request scan IP"),
            BotCommand("scanstatus", "Cek status scan"),
            BotCommand("info", "Cek akun & credits"),
            BotCommand("filters", "Referensi filter Shodan"),
            BotCommand("help", "Tampilkan bantuan"),
        ]
        await app.bot.set_my_commands(commands)
        print(f"✅ Webhook {'set' if result else 'FAILED'}: {url}")


async def remove_webhook():
    """Remove webhook from Telegram."""
    app = build_application()
    async with app:
        result = await app.bot.delete_webhook(drop_pending_updates=True)
        print(f"✅ Webhook {'removed' if result else 'FAILED'}")


def main():
    """Main entry point."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN not set! "
            "Copy .env.example to .env and fill in your tokens."
        )
        return
    if not SHODAN_API_KEY:
        logger.error(
            "❌ SHODAN_API_KEY not set! "
            "Copy .env.example to .env and fill in your tokens."
        )
        return

    # Handle CLI arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup" and len(sys.argv) > 2:
            asyncio.run(setup_webhook(sys.argv[2]))
            return
        elif sys.argv[1] == "--remove":
            asyncio.run(remove_webhook())
            return
        elif sys.argv[1] == "--help":
            print(__doc__)
            return

    # Default: polling mode for local development
    logger.info("🚀 Starting Shodan Telegram Bot (polling mode)...")
    logger.info("   For Azure Functions, deploy with function_app.py")

    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
