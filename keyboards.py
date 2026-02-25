"""
Keyboard builder — creates all inline keyboards for the bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from templates import (
    CATEGORIES,
    TEMPLATES,
    get_template_by_id,
    get_templates_by_category,
    SearchTemplate,
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🔍 Quick Search", callback_data="menu:templates"),
            InlineKeyboardButton("📡 Host Lookup", callback_data="menu:host"),
        ],
        [
            InlineKeyboardButton("📋 DNS Tools", callback_data="menu:dns"),
            InlineKeyboardButton("💥 Exploits", callback_data="menu:exploits"),
        ],
        [
            InlineKeyboardButton("🛡️ Vuln Search", callback_data="menu:vuln"),
            InlineKeyboardButton("📊 Count Query", callback_data="menu:count"),
        ],
        [
            InlineKeyboardButton("⚙️ Raw Query", callback_data="menu:raw"),
            InlineKeyboardButton("ℹ️ Account Info", callback_data="cmd:info"),
        ],
        [
            InlineKeyboardButton("📖 Filter Reference", callback_data="cmd:filters"),
            InlineKeyboardButton("❓ Help", callback_data="cmd:help"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def categories_keyboard() -> InlineKeyboardMarkup:
    """Create category selection keyboard."""
    sorted_cats = sorted(CATEGORIES.items(), key=lambda x: x[1]["order"])
    buttons = []
    row = []
    for cat_id, cat_info in sorted_cats:
        templates_in_cat = get_templates_by_category(cat_id)
        if not templates_in_cat:
            continue
        btn = InlineKeyboardButton(
            f"{cat_info['name']} ({len(templates_in_cat)})",
            callback_data=f"cat:{cat_id}",
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def templates_in_category_keyboard(category: str) -> InlineKeyboardMarkup:
    """Create keyboard with templates in a category."""
    templates = get_templates_by_category(category)
    buttons = []
    for tmpl in templates:
        buttons.append([
            InlineKeyboardButton(
                f"{tmpl.emoji} {tmpl.name}",
                callback_data=f"tmpl:{tmpl.id}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Kembali ke Kategori", callback_data="menu:templates")])
    return InlineKeyboardMarkup(buttons)


def template_detail_keyboard(template: SearchTemplate) -> InlineKeyboardMarkup:
    """Show template details with 'use' and 'example' buttons."""
    buttons = [
        [
            InlineKeyboardButton("✏️ Gunakan Template", callback_data=f"use:{template.id}"),
            InlineKeyboardButton("⚡ Jalankan Contoh", callback_data=f"example:{template.id}"),
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data=f"cat:{template.category}")],
    ]
    return InlineKeyboardMarkup(buttons)


def pagination_keyboard(query: str, current_page: int, total: int, per_page: int = 5) -> InlineKeyboardMarkup:
    """Create pagination keyboard for search results."""
    total_pages = max(1, (total + per_page - 1) // per_page)
    buttons = []
    row = []

    if current_page > 1:
        row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{current_page - 1}:{query}"))

    row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"))

    if current_page < total_pages and current_page < 10:  # Limit to 10 pages
        row.append(InlineKeyboardButton("➡️ Next", callback_data=f"page:{current_page + 1}:{query}"))

    buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Simple back to main menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu:main")]
    ])


def dns_menu_keyboard() -> InlineKeyboardMarkup:
    """DNS tools menu."""
    buttons = [
        [
            InlineKeyboardButton("🔍 DNS Resolve", callback_data="dns:resolve"),
            InlineKeyboardButton("🔄 Reverse DNS", callback_data="dns:reverse"),
        ],
        [
            InlineKeyboardButton("🌐 Domain Info", callback_data="dns:domain"),
        ],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_scan_keyboard(ip: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard before scanning."""
    buttons = [
        [
            InlineKeyboardButton("✅ Ya, Scan!", callback_data=f"doscan:{ip}"),
            InlineKeyboardButton("❌ Batal", callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
