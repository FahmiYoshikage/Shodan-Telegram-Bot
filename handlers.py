"""
All Telegram bot command & callback handlers.
Extracted from bot.py so it can be shared between polling (bot.py) and webhook (function_app.py).
"""

import logging
import asyncio
import traceback
from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

from config import AUTHORIZED_USERS, EMOJI
from shodan_client import shodan_client
from formatter import (
    format_search_results,
    format_host_info,
    format_dns_resolve,
    format_dns_reverse,
    format_domain_info,
    format_exploits,
    format_api_info,
    format_scan_result,
    format_scan_status,
    format_honeypot_score,
    format_welcome,
    format_filters_help,
    format_facets,
    format_number,
    escape_html,
    header_box,
    key_value,
    section_header,
)
from keyboards import (
    main_menu_keyboard,
    categories_keyboard,
    templates_in_category_keyboard,
    template_detail_keyboard,
    pagination_keyboard,
    back_to_main_keyboard,
    dns_menu_keyboard,
    confirm_scan_keyboard,
)
from templates import (
    get_template_by_id,
    get_templates_by_category,
    search_templates,
    build_query,
    CATEGORIES,
    SearchTemplate,
)

logger = logging.getLogger(__name__)

# ─── Conversation states ────────────────────────────────────
(
    STATE_WAITING_PARAM,
    STATE_WAITING_RAW_QUERY,
    STATE_WAITING_HOST_IP,
    STATE_WAITING_DNS,
    STATE_WAITING_EXPLOIT,
    STATE_WAITING_SCAN_IP,
    STATE_WAITING_HONEYPOT_IP,
    STATE_WAITING_COUNT_QUERY,
) = range(8)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTH DECORATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def authorized(func):
    """Restrict access to authorized users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            msg = (
                f"{EMOJI['error']} <b>Akses ditolak.</b>\n"
                f"User ID kamu: <code>{user_id}</code>\n"
                f"Hubungi admin untuk mendapatkan akses."
            )
            if update.callback_query:
                await update.callback_query.answer("⛔ Akses ditolak", show_alert=True)
            else:
                await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        return await func(update, context)
    return wrapper


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPER: SEND LONG MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def send_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    messages: list[str],
    reply_markup=None,
):
    """Send multiple messages, attaching reply_markup to the last one."""
    chat_id = update.effective_chat.id
    for i, msg in enumerate(messages):
        markup = reply_markup if i == len(messages) - 1 else None
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=msg[:4000],
                    reply_markup=markup,
                )
            except Exception as e2:
                logger.error(f"Error sending fallback message: {e2}")


async def reply_html(update: Update, text: str, reply_markup=None):
    """Reply with HTML parse mode."""
    try:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(f"HTML reply error: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMMAND HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_html(update, format_welcome(), main_menu_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_html(update, format_welcome(), main_menu_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{header_box('Template Pencarian', 'Pilih kategori di bawah')}\n\n"
        f"{EMOJI['info']} Pilih kategori untuk melihat template pencarian yang tersedia:"
    )
    await reply_html(update, text, categories_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['search']} <b>Pencarian Shodan</b>\n\n"
            f"Kirim query Shodan langsung.\n"
            f'<i>Contoh: product:"nginx" country:"ID"</i>',
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "raw_query"
        return STATE_WAITING_RAW_QUERY
    query = " ".join(args)
    await _execute_search(update, context, query, page=1)
    return ConversationHandler.END


@authorized
async def cmd_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['stats']} <b>Count Query</b>\n\n"
            f"Kirim query untuk di-count (tanpa pakai query credits).\n"
            f'<i>Contoh: country:"ID" port:22</i>',
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "count_query"
        return STATE_WAITING_COUNT_QUERY
    query = " ".join(args)
    await _execute_count(update, context, query)
    return ConversationHandler.END


@authorized
async def cmd_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['host']} <b>Host Lookup</b>\n\n"
            f"Kirim IP address untuk lookup.\n<i>Contoh: 8.8.8.8</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "host_ip"
        return STATE_WAITING_HOST_IP
    await _execute_host(update, context, args[0])
    return ConversationHandler.END


@authorized
async def cmd_dns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['dns']} <b>DNS Resolve</b>\n\n"
            f"Kirim hostname untuk resolve ke IP.\n<i>Contoh: google.com</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_resolve"
        return STATE_WAITING_DNS
    data = shodan_client.dns_resolve([args[0]])
    await reply_html(update, format_dns_resolve(data), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_rdns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['dns']} <b>Reverse DNS</b>\n\n"
            f"Kirim IP untuk reverse DNS lookup.\n<i>Contoh: 8.8.8.8</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_reverse"
        return STATE_WAITING_DNS
    data = shodan_client.dns_reverse([args[0]])
    await reply_html(update, format_dns_reverse(data), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['globe']} <b>Domain Info</b>\n\n"
            f"Kirim domain untuk lihat DNS records.\n<i>Contoh: example.com</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_domain"
        return STATE_WAITING_DNS
    data = shodan_client.dns_domain(args[0])
    await reply_html(update, format_domain_info(data), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_exploit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['exploit']} <b>Exploit Search</b>\n\n"
            f"Kirim keyword untuk cari exploit.\n<i>Contoh: apache 2.4</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "exploit_query"
        return STATE_WAITING_EXPLOIT
    data = shodan_client.search_exploits(" ".join(args))
    await send_messages(update, context, format_exploits(data), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_honeypot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['honeypot']} <b>Honeypot Detection</b>\n\n"
            f"Kirim IP untuk cek honeypot score.\n<i>Contoh: 1.2.3.4</i>",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "honeypot_ip"
        return STATE_WAITING_HONEYPOT_IP
    score = shodan_client.honeypot_score(args[0])
    await reply_html(update, format_honeypot_score(args[0], score), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['ip']} <b>Request Scan</b>\n\n"
            f"Kirim IP/CIDR untuk request scan.\n<i>Contoh: 1.2.3.4</i>\n\n"
            f"{EMOJI['warning']} <b>Perhatian:</b> Scan menggunakan scan credits!",
            back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "scan_ip"
        return STATE_WAITING_SCAN_IP
    ip = args[0]
    text = (
        f"{EMOJI['warning']} <b>Konfirmasi Scan</b>\n\n"
        f"Apakah kamu yakin ingin scan <code>{escape_html(ip)}</code>?\n"
        f"Ini akan menggunakan scan credits."
    )
    await reply_html(update, text, confirm_scan_keyboard(ip))
    return ConversationHandler.END


@authorized
async def cmd_scanstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await reply_html(
            update,
            f"{EMOJI['info']} <b>Scan Status</b>\n\n"
            f"Kirim scan ID untuk cek status.\n<i>Contoh: /scanstatus abc123</i>",
            back_to_main_keyboard(),
        )
        return ConversationHandler.END
    data = shodan_client.scan_status(args[0])
    await reply_html(update, format_scan_status(data), back_to_main_keyboard())
    return ConversationHandler.END


@authorized
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        info = await asyncio.to_thread(shodan_client.api_info)
        await reply_html(update, format_api_info(info), back_to_main_keyboard())
    except Exception as e:
        logger.error(f"Info error: {e}")
        await reply_html(
            update,
            f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}",
            back_to_main_keyboard(),
        )
    return ConversationHandler.END


@authorized
async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_html(update, format_filters_help(), back_to_main_keyboard())
    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CALLBACK QUERY HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@authorized
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # ─── Navigation ─────────────────────────────────────────
    if data == "menu:main":
        await query.message.reply_text(
            format_welcome(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
        )
        return ConversationHandler.END

    if data == "menu:templates":
        text = f"{header_box('Template Pencarian', 'Pilih kategori')}\n\n{EMOJI['info']} Pilih kategori di bawah:"
        await query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=categories_keyboard(),
        )
        return ConversationHandler.END

    if data == "menu:host":
        await query.message.reply_text(
            f"{EMOJI['host']} <b>Host Lookup</b>\n\nKirim IP address:\n<i>Contoh: 8.8.8.8</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "host_ip"
        return STATE_WAITING_HOST_IP

    if data == "menu:dns":
        await query.message.reply_text(
            f"{EMOJI['dns']} <b>DNS Tools</b>\n\nPilih tool DNS:",
            parse_mode=ParseMode.HTML,
            reply_markup=dns_menu_keyboard(),
        )
        return ConversationHandler.END

    if data == "menu:exploits":
        await query.message.reply_text(
            f"{EMOJI['exploit']} <b>Exploit Search</b>\n\nKirim keyword:\n<i>Contoh: apache 2.4</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "exploit_query"
        return STATE_WAITING_EXPLOIT

    if data == "menu:vuln":
        vuln_templates = get_templates_by_category("vuln")
        buttons = []
        for t in vuln_templates:
            buttons.append([
                InlineKeyboardButton(f"{t.emoji} {t.name}", callback_data=f"tmpl:{t.id}")
            ])
        buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu:main")])
        await query.message.reply_text(
            f"{EMOJI['vuln']} <b>Vulnerability Search</b>\n\nPilih template:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return ConversationHandler.END

    if data == "menu:raw":
        await query.message.reply_text(
            f"{EMOJI['gear']} <b>Raw Shodan Query</b>\n\n"
            f"Kirim query Shodan langsung:\n"
            f'<i>Contoh: product:"nginx" country:"ID" port:443</i>\n\n'
            f"{EMOJI['info']} Gunakan /filters untuk lihat daftar filter.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "raw_query"
        return STATE_WAITING_RAW_QUERY

    if data == "menu:count":
        await query.message.reply_text(
            f"{EMOJI['stats']} <b>Count Query</b>\n\n"
            f"Kirim query untuk di-count (tanpa pakai credits):\n"
            f'<i>Contoh: country:"ID" port:22</i>',
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "count_query"
        return STATE_WAITING_COUNT_QUERY

    # ─── Commands via callback ──────────────────────────────
    if data == "cmd:info":
        try:
            info = await asyncio.to_thread(shodan_client.api_info)
            await query.message.reply_text(
                format_api_info(info),
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_main_keyboard(),
            )
        except Exception as e:
            logger.error(f"Info callback error: {e}")
            await query.message.reply_text(
                f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}",
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_main_keyboard(),
            )
        return ConversationHandler.END

    if data == "cmd:filters":
        await query.message.reply_text(
            format_filters_help(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
            disable_web_page_preview=True,
        )
        return ConversationHandler.END

    if data == "cmd:help":
        await query.message.reply_text(
            format_welcome(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
        )
        return ConversationHandler.END

    # ─── Category selection ─────────────────────────────────
    if data.startswith("cat:"):
        cat_id = data[4:]
        cat_info = CATEGORIES.get(cat_id, {"name": cat_id})
        text = f"{EMOJI['search']} <b>{escape_html(cat_info['name'])}</b>\n\nPilih template:"
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=templates_in_category_keyboard(cat_id),
        )
        return ConversationHandler.END

    # ─── Template detail ────────────────────────────────────
    if data.startswith("tmpl:"):
        tmpl_id = data[5:]
        tmpl = get_template_by_id(tmpl_id)
        if not tmpl:
            await query.message.reply_text(f"{EMOJI['error']} Template tidak ditemukan.")
            return ConversationHandler.END
        await query.message.reply_text(
            format_template_detail(tmpl),
            parse_mode=ParseMode.HTML,
            reply_markup=template_detail_keyboard(tmpl),
        )
        return ConversationHandler.END

    # ─── Use template ───────────────────────────────────────
    if data.startswith("use:"):
        tmpl_id = data[4:]
        tmpl = get_template_by_id(tmpl_id)
        if not tmpl:
            await query.message.reply_text(f"{EMOJI['error']} Template tidak ditemukan.")
            return ConversationHandler.END
        context.user_data["current_template"] = tmpl_id
        context.user_data["template_values"] = {}
        context.user_data["param_index"] = 0
        return await _ask_next_param(update, context)

    # ─── Run example ────────────────────────────────────────
    if data.startswith("example:"):
        tmpl_id = data[8:]
        tmpl = get_template_by_id(tmpl_id)
        if not tmpl:
            await query.message.reply_text(f"{EMOJI['error']} Template tidak ditemukan.")
            return ConversationHandler.END
        await query.message.reply_text(
            f"⏳ <i>Menjalankan: <code>{escape_html(tmpl.example)}</code></i>",
            parse_mode=ParseMode.HTML,
        )
        await _execute_search(update, context, tmpl.example, page=1, facets=tmpl.facets)
        return ConversationHandler.END

    # ─── Pagination ─────────────────────────────────────────
    if data.startswith("page:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            page = int(parts[1])
            search_query = parts[2]
            await _execute_search(update, context, search_query, page=page)
        return ConversationHandler.END

    # ─── DNS callbacks ──────────────────────────────────────
    if data == "dns:resolve":
        await query.message.reply_text(
            f"{EMOJI['dns']} <b>DNS Resolve</b>\n\nKirim hostname:\n<i>Contoh: google.com</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_resolve"
        return STATE_WAITING_DNS

    if data == "dns:reverse":
        await query.message.reply_text(
            f"{EMOJI['dns']} <b>Reverse DNS</b>\n\nKirim IP address:\n<i>Contoh: 8.8.8.8</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_reverse"
        return STATE_WAITING_DNS

    if data == "dns:domain":
        await query.message.reply_text(
            f"{EMOJI['globe']} <b>Domain Info</b>\n\nKirim domain:\n<i>Contoh: example.com</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
        context.user_data["awaiting"] = "dns_domain"
        return STATE_WAITING_DNS

    # ─── Scan confirm ───────────────────────────────────────
    if data.startswith("doscan:"):
        ip = data[7:]
        try:
            result = await asyncio.to_thread(shodan_client.scan_ip, ip)
            await query.message.reply_text(
                format_scan_result(result),
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_main_keyboard(),
            )
        except Exception as e:
            logger.error(f"Scan callback error: {e}")
            await query.message.reply_text(
                f"{EMOJI['error']} <b>Error saat scan:</b> {escape_html(str(e))}",
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_main_keyboard(),
            )
        return ConversationHandler.END

    if data == "noop":
        return ConversationHandler.END

    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEMPLATE PARAM FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _ask_next_param(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask user for the next template parameter."""
    tmpl_id = context.user_data.get("current_template")
    tmpl = get_template_by_id(tmpl_id)
    if not tmpl:
        return ConversationHandler.END

    idx = context.user_data.get("param_index", 0)
    values = context.user_data.get("template_values", {})

    if idx >= len(tmpl.params):
        query = build_query(tmpl, values)
        msg_target = update.callback_query.message if update.callback_query else update.message
        await msg_target.reply_text(
            f"⏳ <i>Menjalankan: <code>{escape_html(query)}</code></i>",
            parse_mode=ParseMode.HTML,
        )
        await _execute_search(update, context, query, page=1, facets=tmpl.facets)
        context.user_data.pop("current_template", None)
        context.user_data.pop("template_values", None)
        context.user_data.pop("param_index", None)
        return ConversationHandler.END

    param = tmpl.params[idx]

    progress_parts = []
    for i, p in enumerate(tmpl.params):
        if i < idx:
            val = values.get(p.name, "?")
            progress_parts.append(
                f"  {EMOJI['success']} <b>{p.name}:</b> <code>{escape_html(val)}</code>"
            )
        elif i == idx:
            progress_parts.append(
                f"  {EMOJI['right']} <b>{p.name}:</b> <i>(menunggu input...)</i>"
            )
        else:
            progress_parts.append(f"  {EMOJI['dot']} <b>{p.name}:</b> <i>-</i>")

    text = (
        f"{EMOJI['gear']} <b>Template: {escape_html(tmpl.name)}</b>\n"
        f"{'─' * 28}\n"
        f"\n<b>Progress:</b>\n" + "\n".join(progress_parts) + "\n\n"
        f"{'─' * 28}\n"
        f"{EMOJI['right']} <b>Masukkan {escape_html(param.description)}:</b>\n"
        f"<i>Contoh: <code>{escape_html(param.placeholder)}</code></i>"
    )

    msg_target = update.callback_query.message if update.callback_query else update.message
    await msg_target.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"💡 Pakai default: {param.placeholder}",
                callback_data=f"default:{param.name}:{param.placeholder}",
            )],
            [InlineKeyboardButton("❌ Batal", callback_data="menu:main")],
        ]),
    )
    context.user_data["awaiting"] = "template_param"
    return STATE_WAITING_PARAM


@authorized
async def handle_param_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle parameter text input from user."""
    awaiting = context.user_data.get("awaiting", "")

    if awaiting == "template_param":
        value = update.message.text.strip()
        tmpl_id = context.user_data.get("current_template")
        tmpl = get_template_by_id(tmpl_id)
        if not tmpl:
            return ConversationHandler.END
        idx = context.user_data.get("param_index", 0)
        param = tmpl.params[idx]
        context.user_data["template_values"][param.name] = value
        context.user_data["param_index"] = idx + 1
        return await _ask_next_param(update, context)

    elif awaiting == "raw_query":
        query = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        await update.message.reply_text(
            f"⏳ <i>Mencari: <code>{escape_html(query)}</code></i>",
            parse_mode=ParseMode.HTML,
        )
        await _execute_search(update, context, query, page=1)
        return ConversationHandler.END

    elif awaiting == "count_query":
        query = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        await _execute_count(update, context, query)
        return ConversationHandler.END

    elif awaiting == "host_ip":
        ip = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        await _execute_host(update, context, ip)
        return ConversationHandler.END

    elif awaiting == "dns_resolve":
        hostname = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        try:
            data = await asyncio.to_thread(shodan_client.dns_resolve, [hostname])
            await reply_html(update, format_dns_resolve(data), back_to_main_keyboard())
        except Exception as e:
            logger.error(f"DNS resolve error: {e}")
            await reply_html(update, f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}", back_to_main_keyboard())
        return ConversationHandler.END

    elif awaiting == "dns_reverse":
        ip = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        try:
            data = await asyncio.to_thread(shodan_client.dns_reverse, [ip])
            await reply_html(update, format_dns_reverse(data), back_to_main_keyboard())
        except Exception as e:
            logger.error(f"DNS reverse error: {e}")
            await reply_html(update, f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}", back_to_main_keyboard())
        return ConversationHandler.END

    elif awaiting == "dns_domain":
        domain = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        try:
            data = await asyncio.to_thread(shodan_client.dns_domain, domain)
            await reply_html(update, format_domain_info(data), back_to_main_keyboard())
        except Exception as e:
            logger.error(f"DNS domain error: {e}")
            await reply_html(update, f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}", back_to_main_keyboard())
        return ConversationHandler.END

    elif awaiting == "exploit_query":
        query = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        try:
            data = await asyncio.to_thread(shodan_client.search_exploits, query)
            await send_messages(update, context, format_exploits(data), back_to_main_keyboard())
        except Exception as e:
            logger.error(f"Exploit search error: {e}")
            await reply_html(update, f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}", back_to_main_keyboard())
        return ConversationHandler.END

    elif awaiting == "honeypot_ip":
        ip = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        try:
            score = await asyncio.to_thread(shodan_client.honeypot_score, ip)
            await reply_html(update, format_honeypot_score(ip, score), back_to_main_keyboard())
        except Exception as e:
            logger.error(f"Honeypot score error: {e}")
            await reply_html(update, f"{EMOJI['error']} <b>Error:</b> {escape_html(str(e))}", back_to_main_keyboard())
        return ConversationHandler.END

    elif awaiting == "scan_ip":
        ip = update.message.text.strip()
        context.user_data.pop("awaiting", None)
        text = (
            f"{EMOJI['warning']} <b>Konfirmasi Scan</b>\n\n"
            f"Scan <code>{escape_html(ip)}</code>?\nIni menggunakan scan credits."
        )
        await reply_html(update, text, confirm_scan_keyboard(ip))
        return ConversationHandler.END

    # Default: raw search
    query = update.message.text.strip()
    if query.startswith("/"):
        return ConversationHandler.END
    await _execute_search(update, context, query, page=1)
    return ConversationHandler.END


@authorized
async def handle_default_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle default parameter button press."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("default:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            param_name = parts[1]
            param_value = parts[2]
            tmpl_id = context.user_data.get("current_template")
            tmpl = get_template_by_id(tmpl_id)
            if not tmpl:
                return ConversationHandler.END
            context.user_data["template_values"][param_name] = param_value
            idx = context.user_data.get("param_index", 0)
            context.user_data["param_index"] = idx + 1
            return await _ask_next_param(update, context)

    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EXECUTION HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _execute_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    page: int = 1,
    facets: str = "",
):
    try:
        data = await asyncio.to_thread(shodan_client.search, query, page=page, facets=facets)
        if "error" in data:
            await reply_html(
                update,
                f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}",
                back_to_main_keyboard(),
            )
            return
        messages = format_search_results(data, page)
        total = data.get("total", 0)
        markup = pagination_keyboard(query, page, total) if total > 0 else back_to_main_keyboard()
        await send_messages(update, context, messages, markup)
    except Exception as e:
        logger.error(f"Search execution error: {e}\n{traceback.format_exc()}")
        await reply_html(
            update,
            f"{EMOJI['error']} <b>Error saat pencarian:</b>\n<code>{escape_html(str(e))}</code>",
            back_to_main_keyboard(),
        )


async def _execute_count(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        data = await asyncio.to_thread(shodan_client.search_count, query, facets="org:10,port:10,country:10")
        if "error" in data:
            await reply_html(
                update,
                f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}",
                back_to_main_keyboard(),
            )
            return
        total = data.get("total", 0)
        facets_data = data.get("facets", {})
        text = header_box("Count Result", f"Query: {query}")
        text += f"\n\n{EMOJI['stats']} <b>Total:</b> {format_number(total)} hasil ditemukan"
        text += f"\n{EMOJI['info']} <i>Count tidak menggunakan query credits!</i>"
        if facets_data:
            text += format_facets(facets_data)
        await reply_html(update, text, back_to_main_keyboard())
    except Exception as e:
        logger.error(f"Count execution error: {e}\n{traceback.format_exc()}")
        await reply_html(
            update,
            f"{EMOJI['error']} <b>Error saat count:</b>\n<code>{escape_html(str(e))}</code>",
            back_to_main_keyboard(),
        )


async def _execute_host(update: Update, context: ContextTypes.DEFAULT_TYPE, ip: str):
    try:
        await reply_html(update, f"⏳ <i>Looking up <code>{escape_html(ip)}</code>...</i>")
        data = await asyncio.to_thread(shodan_client.host_info, ip)
        if "error" in data:
            await reply_html(
                update,
                f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}",
                back_to_main_keyboard(),
            )
            return
        messages = format_host_info(data)
        await send_messages(update, context, messages, back_to_main_keyboard())
    except Exception as e:
        logger.error(f"Host lookup error: {e}\n{traceback.format_exc()}")
        await reply_html(
            update,
            f"{EMOJI['error']} <b>Error saat host lookup:</b>\n<code>{escape_html(str(e))}</code>",
            back_to_main_keyboard(),
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEMPLATE DETAIL FORMATTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_template_detail(tmpl: SearchTemplate) -> str:
    params_text = ""
    for p in tmpl.params:
        req = "wajib" if p.required else "opsional"
        params_text += (
            f"  {EMOJI['right']} <b>{escape_html(p.name)}</b> — "
            f"{escape_html(p.description)} ({req})\n"
            f"     <i>Contoh: <code>{escape_html(p.placeholder)}</code></i>\n"
        )
    return (
        f"{tmpl.emoji} <b>{escape_html(tmpl.name)}</b>\n"
        f"{'─' * 28}\n\n"
        f"{EMOJI['info']} {escape_html(tmpl.description)}\n\n"
        f"{EMOJI['gear']} <b>Parameter:</b>\n{params_text}\n"
        f"{EMOJI['search']} <b>Query template:</b>\n"
        f"  <code>{escape_html(tmpl.query_template)}</code>\n\n"
        f"{EMOJI['star']} <b>Contoh query:</b>\n"
        f"  <code>{escape_html(tmpl.example)}</code>"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GLOBAL ERROR HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler — catches any unhandled exception and notifies the user."""
    logger.error(f"Unhandled exception: {context.error}\n{traceback.format_exc()}")

    if not isinstance(update, Update) or not update.effective_chat:
        return

    try:
        error_msg = str(context.error) if context.error else "Unknown error"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"{EMOJI['error']} <b>Terjadi error:</b>\n"
                f"<code>{escape_html(error_msg[:500])}</code>\n\n"
                f"<i>Silakan coba lagi atau gunakan /start</i>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_main_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")
