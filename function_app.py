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

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WEBHOOK ENDPOINT — Receives Telegram updates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="webhook", methods=["POST"])
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main webhook handler — receives updates from Telegram.
    Telegram sends POST requests to this endpoint for every message/callback.
    """
    try:
        telegram_app = await get_application()

        # Parse the incoming update
        body = req.get_body().decode("utf-8")
        update_data = json.loads(body)
        update = Update.de_json(data=update_data, bot=telegram_app.bot)

        # Process the update
        async with telegram_app:
            await telegram_app.process_update(update)

        return func.HttpResponse(status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=200,  # Always return 200 to Telegram to prevent retries
            mimetype="application/json",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SET WEBHOOK — Call this once to register webhook URL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="setup", methods=["GET"])
async def setup_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Setup endpoint — registers the webhook with Telegram.
    Call this once after deployment:
    GET https://<your-func>.azurewebsites.net/api/setup?url=<webhook_url>
    """
    try:
        telegram_app = await get_application()

        # Get webhook URL from query param or construct from environment
        webhook_url = req.params.get("url", "")
        if not webhook_url:
            # Auto-construct from Azure Function URL
            func_url = os.getenv("WEBSITE_HOSTNAME", "")
            func_key = os.getenv("WEBHOOK_FUNCTION_KEY", "")
            if func_url:
                webhook_url = f"https://{func_url}/api/webhook"
                if func_key:
                    webhook_url += f"?code={func_key}"

        if not webhook_url:
            return func.HttpResponse(
                body=json.dumps({
                    "error": "No webhook URL provided.",
                    "usage": "GET /api/setup?url=https://your-func.azurewebsites.net/api/webhook?code=YOUR_KEY"
                }),
                status_code=400,
                mimetype="application/json",
            )

        async with telegram_app:
            # Set webhook
            result = await telegram_app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
            )

            # Set bot commands for nice menu in Telegram
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
                "message": "Webhook registered successfully!" if result else "Failed to set webhook",
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
    from config import SHODAN_API_KEY, TELEGRAM_BOT_TOKEN

    status = {
        "status": "healthy",
        "shodan_configured": bool(SHODAN_API_KEY),
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN),
    }

    # Optionally check Shodan credits
    try:
        from shodan_client import shodan_client
        info = shodan_client.api_info()
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
#  DELETE WEBHOOK — For switching back to polling mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route(route="teardown", methods=["GET"])
async def teardown_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Remove webhook (useful for switching back to polling mode locally)."""
    try:
        telegram_app = await get_application()
        async with telegram_app:
            result = await telegram_app.bot.delete_webhook(drop_pending_updates=True)

        return func.HttpResponse(
            body=json.dumps({
                "success": result,
                "message": "Webhook removed. You can now use polling mode locally.",
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
