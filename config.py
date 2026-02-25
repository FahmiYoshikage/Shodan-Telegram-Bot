"""
Configuration module for Shodan Telegram Bot.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_USERS = [
    int(uid.strip())
    for uid in os.getenv("AUTHORIZED_USERS", "").split(",")
    if uid.strip().isdigit()
]

# ─── Shodan ─────────────────────────────────────────────────
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")

# ─── Logging ────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─── Display ────────────────────────────────────────────────
MAX_RESULTS_PER_PAGE = 5
MAX_MESSAGE_LENGTH = 4000  # Telegram limit ~4096

# ─── Emojis for pretty output ───────────────────────────────
EMOJI = {
    "search": "🔍",
    "host": "🖥️",
    "ip": "📡",
    "port": "🔌",
    "vuln": "🛡️",
    "country": "🌍",
    "city": "🏙️",
    "org": "🏢",
    "isp": "📶",
    "os": "💻",
    "product": "📦",
    "version": "🏷️",
    "ssl": "🔒",
    "warning": "⚠️",
    "error": "❌",
    "success": "✅",
    "info": "ℹ️",
    "stats": "📊",
    "globe": "🌐",
    "key": "🔑",
    "time": "🕐",
    "tag": "🏷️",
    "link": "🔗",
    "dns": "📋",
    "exploit": "💥",
    "camera": "📷",
    "database": "🗄️",
    "industrial": "🏭",
    "honeypot": "🍯",
    "star": "⭐",
    "fire": "🔥",
    "lock": "🔐",
    "unlock": "🔓",
    "chart": "📈",
    "folder": "📁",
    "gear": "⚙️",
    "rocket": "🚀",
    "wave": "👋",
    "down": "⬇️",
    "right": "▶️",
    "check": "☑️",
    "dot": "◽",
    "arrow": "➜",
    "separator": "─" * 30,
}
