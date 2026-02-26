"""
Azure Functions entry point — Telegram Webhook handler.
Uses Azure Functions v2 Python programming model.
"""

import os
import json
import logging
import azure.functions as func
from telegram import Update

from bot_app import get_application
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WEBHOOK ENDPOINT — Receives Telegram updates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="webhook", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main webhook handler — receives updates from Telegram.
    Auth: ANONYMOUS karena Telegram tidak bisa kirim function key.
    Security: Bot token divalidasi oleh python-telegram-bot library.
    """
    try:
        telegram_app = await get_application()

        # Parse the incoming update
        body = req.get_body().decode("utf-8")
        update_data = json.loads(body)
        update = Update.de_json(data=update_data, bot=telegram_app.bot)

        # Process the update
        await telegram_app.process_update(update)

        return func.HttpResponse(status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=200,  # Always return 200 to prevent Telegram retries
            mimetype="application/json",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SET WEBHOOK — Call once after deployment
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="setup", methods=["GET"])
async def setup_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Setup endpoint — registers the webhook with Telegram.
    Call once after deployment:
    GET https://<your-func>.azurewebsites.net/api/setup?code=<FUNCTION_KEY>
    """
    try:
        telegram_app = await get_application()

        # Auto-construct webhook URL from Azure hostname
        webhook_url = req.params.get("url", "")
        if not webhook_url:
            func_url = os.getenv("WEBSITE_HOSTNAME", "")
            if func_url:
                webhook_url = f"https://{func_url}/api/webhook"

        if not webhook_url:
            return func.HttpResponse(
                body=json.dumps({"error": "Cannot determine webhook URL"}),
                status_code=400,
                mimetype="application/json",
            )

        # Set webhook
        result = await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )

        # Set bot commands
        from telegram import BotCommand
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
        await telegram_app.bot.set_my_commands(commands)

        return func.HttpResponse(
            body=json.dumps({
                "success": result,
                "webhook_url": webhook_url,
                "message": "Webhook registered!" if result else "Failed",
            }),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error setting webhook: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint for monitoring."""
    status = {
        "status": "healthy",
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
    }

    try:
        from shodan_client import shodan_client
        import asyncio
        info = await asyncio.to_thread(shodan_client.api_info)
        status["shodan_plan"] = info.get("plan", "unknown")
        status["query_credits"] = info.get("query_credits", 0)
        status["scan_credits"] = info.get("scan_credits", 0)
    except Exception as e:
        status["shodan_error"] = str(e)

    return func.HttpResponse(
        body=json.dumps(status, indent=2),
        status_code=200,
        mimetype="application/json",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEARDOWN — Remove webhook for switching to polling mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="teardown", methods=["GET"])
async def teardown_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Remove webhook (for switching back to local polling mode)."""
    try:
        telegram_app = await get_application()
        result = await telegram_app.bot.delete_webhook(drop_pending_updates=True)

        return func.HttpResponse(
            body=json.dumps({
                "success": result,
                "message": "Webhook removed. You can now use polling mode.",
            }),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
