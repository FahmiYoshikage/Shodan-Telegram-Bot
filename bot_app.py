"""
Shodan Telegram Bot — Application builder.
Creates the python-telegram-bot Application with all handlers.
Works for both:
  - Azure Functions (webhook mode) → used by function_app.py
  - Local development (polling mode) → used by bot.py
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL

# ─── Logging ────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)

# ─── Singleton application ──────────────────────────────────
_application: Application | None = None


def _build_application() -> Application:
    """Build the Application with all handlers registered."""
    import warnings
    from telegram.warnings import PTBUserWarning
    from handlers import (
        cmd_start, cmd_help, cmd_templates, cmd_search, cmd_count,
        cmd_host, cmd_dns, cmd_rdns, cmd_domain, cmd_exploit,
        cmd_honeypot, cmd_scan, cmd_scanstatus, cmd_info, cmd_filters,
        callback_handler, handle_param_input, handle_default_param,
        error_handler,
        STATE_WAITING_PARAM, STATE_WAITING_RAW_QUERY, STATE_WAITING_HOST_IP,
        STATE_WAITING_DNS, STATE_WAITING_EXPLOIT, STATE_WAITING_SCAN_IP,
        STATE_WAITING_HONEYPOT_IP, STATE_WAITING_COUNT_QUERY,
    )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Suppress per_message warning — we intentionally use per_message=False
    # because our callback handlers don't need per-message tracking.
    warnings.filterwarnings("ignore", category=PTBUserWarning)

    conv_handler = ConversationHandler(
        per_message=False,
        entry_points=[
            CommandHandler("start", cmd_start),
            CommandHandler("help", cmd_help),
            CommandHandler("templates", cmd_templates),
            CommandHandler("t", cmd_templates),
            CommandHandler("search", cmd_search),
            CommandHandler("count", cmd_count),
            CommandHandler("host", cmd_host),
            CommandHandler("dns", cmd_dns),
            CommandHandler("rdns", cmd_rdns),
            CommandHandler("domain", cmd_domain),
            CommandHandler("exploit", cmd_exploit),
            CommandHandler("honeypot", cmd_honeypot),
            CommandHandler("scan", cmd_scan),
            CommandHandler("scanstatus", cmd_scanstatus),
            CommandHandler("info", cmd_info),
            CommandHandler("filters", cmd_filters),
            CallbackQueryHandler(callback_handler),
        ],
        states={
            STATE_WAITING_PARAM: [
                CallbackQueryHandler(handle_default_param, pattern=r"^default:"),
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_RAW_QUERY: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_HOST_IP: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_DNS: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_EXPLOIT: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_SCAN_IP: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_HONEYPOT_IP: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
            STATE_WAITING_COUNT_QUERY: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
            ],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("help", cmd_help),
            CallbackQueryHandler(callback_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_param_input),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    return app


async def get_application() -> Application:
    """
    Get or create the singleton Application instance.
    Used by Azure Functions to reuse across invocations.
    """
    global _application
    if _application is None:
        _application = _build_application()
        await _application.initialize()
    return _application


def build_application() -> Application:
    """
    Build a new Application instance (for polling mode).
    Used by bot.py for local development.
    """
    return _build_application()
