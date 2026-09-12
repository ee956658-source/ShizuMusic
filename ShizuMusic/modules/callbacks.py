# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import enums
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from ShizuMusic import bot, call_py
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import (
    clear_queue,
    peek_current,
    pop_current,
    queue_size,
)
from ShizuMusic.utils.db import is_user_blocked_db
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    rich_edit,
    sanitize_display_name,
)


def _support_updates_pills() -> str:
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        "🍬 sᴜᴘᴘᴏʀᴛ</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 ᴜᴘᴅᴀᴛᴇs</tg-button>"
        "</p>"
    )


# ── Clickable Telegram command helper ─────────────────────────────────────────

def _cmd(command: str) -> str:
    name = command.lstrip("/").split()[0]
    return f'<a href="tg://bot_command?command={name}">{rich_esc(command)}</a>'


# ── Category renderer ─────────────────────────────────────────────────────────

def _category_html(title: str, desc: str, rows, photo: str = None) -> str:
    html = ""

    if photo:
        html += rich_img(photo)

    html += rich_heading(title, level=3)

    if desc:
        html += f"<p>{desc}</p>"

    for command, description in rows:
        if command:
            html += f"<p>{command}<br>→ {description}</p>"
        else:
            html += f"<p>{description}</p>"

    return html


# ── Main Help menu ────────────────────────────────────────────────────────────

_HELP_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "ᴀᴅᴍɪɴ",
            callback_data="help_admin",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "ᴀ-ᴘʟᴀʏ",
            callback_data="help_autoplay",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "ɢ-ᴄᴀsᴛ",
            callback_data="help_gcast",
            style=enums.ButtonStyle.DEFAULT,
        ),
    ],
    [
        InlineKeyboardButton(
            "ʙʟ-ᴄʜᴀᴛ",
            callback_data="help_blchat",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "ʙʟ-ᴜsᴇʀs",
            callback_data="help_blusers",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "ᴘɪɴɢ",
            callback_data="help_ping",
            style=enums.ButtonStyle.DEFAULT,
        ),
    ],
    [
        InlineKeyboardButton(
            "ᴘʟᴀʏ",
            callback_data="help_play",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "sᴘᴇᴇᴅ",
            callback_data="help_speed",
            style=enums.ButtonStyle.DEFAULT,
        ),
        InlineKeyboardButton(
            "ʟᴏᴏᴘ",
            callback_data="help_info",
            style=enums.ButtonStyle.DEFAULT,
        ),
    ],
    [
        InlineKeyboardButton(
            "≡ ᴄʟᴏsᴇ ≡",
            callback_data="close_help",
            style=enums.ButtonStyle.DEFAULT,
        ),
    ],
])


# ── Category keyboard ─────────────────────────────────────────────────────────
# Only CLOSE. No BACK.

_CLOSE_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "≡ ᴄʟᴏsᴇ ≡",
            callback_data="close_help",
            style=enums.ButtonStyle.DEFAULT,
        ),
    ],
])


# ── Help texts ────────────────────────────────────────────────────────────────

_HELP_TEXTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN
    # ─────────────────────────────────────────────────────────────────────────

    "help_admin": {
        "title": "⚙️ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "ᴍᴀɴᴀɢᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴘʟᴀʏʙᴀᴄᴋ ᴡɪᴛʜ ᴇssᴇɴᴛɪᴀʟ ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟs.",
        "rows": [
            (
                _cmd("/pause"),
                "ᴘᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ ᴛʀᴀᴄᴋ",
            ),
            (
                _cmd("/resume"),
                "ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜsᴇᴅ ᴘʟᴀʏʙᴀᴄᴋ",
            ),
            (
                _cmd("/skip"),
                "sᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ ᴀɴᴅ ᴘʟᴀʏ ᴛʜᴇ ɴᴇxᴛ ᴏɴᴇ",
            ),
            (
                _cmd("/stop") + ", " + _cmd("/end"),
                "sᴛᴏᴘ ᴘʟᴀʏʙᴀᴄᴋ ᴀɴᴅ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ",
            ),
            (
                _cmd("/clear"),
                "ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴛʀᴀᴄᴋs ғʀᴏᴍ ᴛʜᴇ ǫᴜᴇᴜᴇ",
            ),
            (
                _cmd("/seek") + " &lt;seconds&gt;",
                "ᴍᴏᴠᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ ғᴏʀᴡᴀʀᴅ ʙʏ ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ sᴇᴄᴏɴᴅs",
            ),
            (
                _cmd("/seekback") + " &lt;seconds&gt;",
                "ᴍᴏᴠᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ ʙᴀᴄᴋᴡᴀʀᴅ ʙʏ ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ sᴇᴄᴏɴᴅs",
            ),
            (
                _cmd("/reboot"),
                "ʀᴇsᴇᴛ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ sᴛᴀᴛᴇ ᴀɴᴅ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # AUTOPLAY
    # ─────────────────────────────────────────────────────────────────────────

    "help_autoplay": {
        "title": "🔁 ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "ᴋᴇᴇᴘ ʏᴏᴜʀ ᴍᴜsɪᴄ ᴘʟᴀʏɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʙᴀsᴇᴅ ᴏɴ ʏᴏᴜʀ ᴄʜᴏsᴇɴ ǫᴜᴇʀʏ. ᴡʜᴇɴ ᴛʜᴇ ǫᴜᴇᴜᴇ ʀᴜɴs ᴏᴜᴛ, ᴀᴜᴛᴏᴘʟᴀʏ ᴡɪʟʟ ғɪɴᴅ ᴀɴᴅ ᴘʟᴀʏ ᴀ ɴᴇᴡ ᴛʀᴀᴄᴋ ᴛᴏ ᴋᴇᴇᴘ ᴛʜᴇ ᴍᴜsɪᴄ ɢᴏɪɴɢ.",
        "rows": [
            (
                _cmd("/autoplay") + " &lt;query&gt;",
                "ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ ᴜsɪɴɢ ʏᴏᴜʀ ᴄʜᴏsᴇɴ ǫᴜᴇʀʏ",
            ),
            (
                _cmd("/end") + ", " + _cmd("/stop"),
                "sᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ ᴀɴᴅ ᴄʟᴇᴀʀ ᴛʜᴇ ǫᴜᴇᴜᴇ",
            ),
            (
                _cmd("/autoplay") + " sidhu moose wala",
                "ᴇxᴀᴍᴘʟᴇ",
            ),
            (
                _cmd("/autoplay") + " arijit singh",
                "ᴇxᴀᴍᴘʟᴇ",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GCAST
    # ─────────────────────────────────────────────────────────────────────────

    "help_gcast": {
        "title": "📢 ɢ-ᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "",
        "rows": [
            (
                _cmd("/broadcast") + " [ᴍᴇssᴀɢᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ]",
                "ʙʀᴏᴀᴅᴄᴀsᴛ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.",
            ),
            (
                "",
                "ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴏᴅᴇs :",
            ),
            (
                "-pin",
                "ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇs ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs.",
            ),
            (
                "-pinloud",
                "ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇ ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴀɴᴅ sᴇɴᴅ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴛᴏ ᴛʜᴇ ᴍᴇᴍʙᴇʀs.",
            ),
            (
                "-user",
                "ʙʀᴏᴀᴅᴄᴀsᴛs ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ᴛʜᴇ ᴜsᴇʀs ᴡʜᴏ ʜᴀᴠᴇ sᴛᴀʀᴛᴇᴅ ʏᴏᴜʀ ʙᴏᴛ.",
            ),
            (
                "-assistant",
                "ʙʀᴏᴀᴅᴄᴀsᴛ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ᴀssɪᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.",
            ),
            (
                "-nobot",
                "ғᴏʀᴄᴇs ᴛʜᴇ ʙᴏᴛ ᴛᴏ ɴᴏᴛ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛʜᴇ ᴍᴇssᴀɢᴇ.",
            ),
            (
                "",
                "ᴇxᴀᴍᴩʟᴇ: "
                + _cmd("/broadcast")
                + " -user -assistant -pin ᴛᴇsᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BLACKLIST CHAT
    # ─────────────────────────────────────────────────────────────────────────

    "help_blchat": {
        "title": "🚫 ʙʟ-ᴄʜᴀᴛ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "",
        "rows": [
            (
                "",
                "**ᴄʜᴀᴛ ʙʟᴀᴄᴋʟɪsᴛ ғᴇᴀᴛᴜʀᴇ :** [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs]",
            ),
            (
                "",
                "ʀᴇsᴛʀɪᴄᴛ sʜɪᴛ ᴄʜᴀᴛs ᴛᴏ ᴜsᴇ ᴏᴜʀ ᴘʀᴇᴄɪᴏᴜs ʙᴏᴛ.",
            ),
            (
                _cmd("/blacklistchat") + " [ᴄʜᴀᴛ ɪᴅ]",
                "ʙʟᴀᴄᴋʟɪsᴛ ᴀ ᴄʜᴀᴛ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.",
            ),
            (
                _cmd("/whitelistchat") + " [ᴄʜᴀᴛ ɪᴅ]",
                "ᴡʜɪᴛᴇʟɪsᴛ ᴛʜᴇ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛ.",
            ),
            (
                _cmd("/blacklistedchat"),
                "sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛs.",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BLACKLIST USERS
    # ─────────────────────────────────────────────────────────────────────────

    "help_blusers": {
        "title": "🚫 ʙʟ-ᴜsᴇʀs ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "",
        "rows": [
            (
                "",
                "**ʙʟᴏᴄᴋ ᴜsᴇʀs:** [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs]",
            ),
            (
                "",
                "sᴛᴀʀᴛs ɪɢɴᴏʀɪɴɢ ᴛʜᴇ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴜsᴇʀ, sᴏ ᴛʜᴀᴛ ʜᴇ ᴄᴀɴ'ᴛ ᴜsᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs.",
            ),
            (
                _cmd("/block") + " [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ]",
                "ʙʟᴏᴄᴋ ᴛʜᴇ ᴜsᴇʀ ғʀᴏᴍ ᴏᴜʀ ʙᴏᴛ.",
            ),
            (
                _cmd("/unblock") + " [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ]",
                "ᴜɴʙʟᴏᴄᴋs ᴛʜᴇ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀ.",
            ),
            (
                _cmd("/blockedusers"),
                "sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs.",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # PING
    # ─────────────────────────────────────────────────────────────────────────

    "help_ping": {
        "title": "🏓 ᴘɪɴɢ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "",
        "rows": [
            (
                _cmd("/start"),
                "sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ.",
            ),
            (
                _cmd("/help"),
                "ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ ᴡɪᴛʜ ᴇxᴩʟᴀɴᴀᴛɪᴏɴ ᴏғ ᴄᴏᴍᴍᴀɴᴅs.",
            ),
            (
                _cmd("/ping"),
                "sʜᴏᴡs ᴛʜᴇ ᴩɪɴɢ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.",
            ),
            (
                _cmd("/stats"),
                "sʜᴏᴡs ᴛʜᴇ ᴏᴠᴇʀᴀʟʟ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # PLAY
    # ─────────────────────────────────────────────────────────────────────────

    "help_play": {
        "title": "🎵 ᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs",
        "desc": "",
        "rows": [
            (
                "",
                "**ᴠ :** sᴛᴀɴᴅs ғᴏʀ ᴠɪᴅᴇᴏ ᴩʟᴀʏ.",
            ),
            (
                "",
                "**ғᴏʀᴄᴇ :** sᴛᴀɴᴅs ғᴏʀ ғᴏʀᴄᴇ ᴩʟᴀʏ.",
            ),
            (
                _cmd("/play") + " ᴏʀ " + _cmd("/vplay"),
                "sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.",
            ),
            (
                _cmd("/playforce") + " ᴏʀ " + _cmd("/vplayforce"),
                "sᴛᴏᴩs ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ.",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SPEED
    # ─────────────────────────────────────────────────────────────────────────

    "help_speed": {
        "title": "🎚️ sᴘᴇᴇᴅ &amp; ᴇғғᴇᴄᴛs",
        "desc": "ᴀᴅᴊᴜsᴛ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ᴀɴᴅ ᴀᴜᴅɪᴏ ᴇғғᴇᴄᴛs.",
        "rows": [
            (
                _cmd("/speed") + " &lt;0.25–4.0&gt;",
                "ᴄʜᴀɴɢᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ — ᴇ.ɢ. /speed 1.5",
            ),
            (
                _cmd("/speedreset"),
                "ʀᴇsᴇᴛ sᴘᴇᴇᴅ ᴛᴏ ɴᴏʀᴍᴀʟ (1.0x)",
            ),
            (
                _cmd("/bass") + " &lt;1–20&gt;",
                "ʙᴏᴏsᴛ ʙᴀss ʙʏ ɴ ᴅʙ — ᴇ.ɢ. /bass 10",
            ),
            (
                _cmd("/bassoff"),
                "ᴛᴜʀɴ ᴏғғ ʙᴀss ʙᴏᴏsᴛ",
            ),
            (
                _cmd("/effecton"),
                "ᴀᴘᴘʟʏ ᴇғғᴇᴄᴛs ᴛᴏ ᴀʟʟ sᴏɴɢs",
            ),
            (
                _cmd("/effectoff"),
                "ᴅɪsᴀʙʟᴇ ᴀᴜᴛᴏ ᴇғғᴇᴄᴛs",
            ),
            (
                _cmd("/effects"),
                "sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ᴇғғᴇᴄᴛ sᴛᴀᴛᴜs",
            ),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LOOP
    # ─────────────────────────────────────────────────────────────────────────

    "help_info": {
        "title": "🔁 ʟᴏᴏᴘ sᴛʀᴇᴀᴍ",
        "desc": "",
        "rows": [
            (
                "",
                "**ʟᴏᴏᴘ sᴛʀᴇᴀᴍ :**",
            ),
            (
                "",
                "sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ",
            ),
            (
                _cmd("/loop") + " [enable/disable]",
                "ᴇɴᴀʙʟᴇs/ᴅɪsᴀʙʟᴇs ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ",
            ),
            (
                _cmd("/loop") + " [1, 2, 3, ...]",
                "ᴇɴᴀʙʟᴇs ᴛʜᴇ ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ɢɪᴠᴇɴ ᴠᴀʟᴜᴇ.",
            ),
        ],
    },
}


# ═════════════════════════════════════════════════════════════════════════════
# MAIN CALLBACK HANDLER
# ═════════════════════════════════════════════════════════════════════════════

@bot.on_callback_query()
async def on_callback(client, cbq: CallbackQuery) -> None:

    chat_id = cbq.message.chat.id
    user = cbq.from_user
    data = cbq.data

    # ── Block check ──────────────────────────────────────────────────────────

    if user and is_user_blocked_db(user.id):
        await cbq.answer()
        return

    # ── Admin check for playback controls ────────────────────────────────────

    if data in ("pause", "resume", "skip", "stop", "clear"):
        if not await is_user_authorized(cbq):
            await cbq.answer(
                "❍ ᴀᴅᴍɪɴs ᴏɴʟʏ",
                show_alert=True,
            )
            return

    # ── PAUSE ────────────────────────────────────────────────────────────────

    if data == "pause":
        try:
            await call_py.pause(chat_id)

            await cbq.answer("ᴘᴀᴜsᴇᴅ")

            await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "⏸ ˢᵗʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ",
                    level=3,
                )
                + rich_note(
                    f"❍ ʙʏ » {user.mention}"
                ),
            )

        except Exception:
            await cbq.answer(
                "ғᴀɪʟᴇᴅ ᴛᴏ ᴘᴀᴜsᴇ",
                show_alert=True,
            )

    # ── RESUME ───────────────────────────────────────────────────────────────

    elif data == "resume":
        try:
            await call_py.resume(chat_id)

            await cbq.answer("ʀᴇsᴜᴍᴇᴅ")

            await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "▶ sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ",
                    level=3,
                )
                + rich_note(
                    f"❍ ʙʏ » {user.mention}"
                ),
            )

        except Exception:
            await cbq.answer(
                "ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇsᴜᴍᴇ",
                show_alert=True,
            )

    # ── SKIP ─────────────────────────────────────────────────────────────────

    elif data == "skip":

        if not queue_size(chat_id):
            await cbq.answer(
                "ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ",
                show_alert=True,
            )
            return

        skipped = pop_current(chat_id)

        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass

        await asyncio.sleep(2)

        try:
            delete_file(
                skipped.get(
                    "file_path",
                    "",
                )
            )
        except Exception:
            pass

        await rich_send(
            bot,
            chat_id,
            f"<p>⏭️ <b>Stream skipped by</b> "
            f"{user.mention}</p>",
        )

        nxt = peek_current(chat_id)

        if nxt:
            await cbq.answer(
                "ᴘʟᴀʏɪɴɢ ɴᴇxᴛ"
            )

            dm = await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "⏭ ɴᴇxᴛ ᴛʀᴀᴄᴋ",
                    level=3,
                ),
            )

            await play_song(
                chat_id,
                dm,
                nxt,
            )

        else:
            await cbq.answer(
                "sᴋɪᴘᴘᴇᴅ"
            )

    # ── STOP ─────────────────────────────────────────────────────────────────

    elif data == "stop":

        await leave_vc(chat_id)

        await cbq.answer(
            "sᴛᴏᴘᴘᴇᴅ"
        )

        await rich_send(
            bot,
            chat_id,
            rich_heading(
                "⏹ ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ",
                level=3,
            )
            + rich_note(
                f"❍ ʙʏ » {user.mention}"
            ),
        )

    # ── CLEAR ────────────────────────────────────────────────────────────────

    elif data == "clear":

        clear_queue(chat_id)

        await cbq.answer(
            "ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ"
        )

        await rich_edit(
            cbq.message,
            rich_heading(
                "🧹 ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ",
                level=3,
            )
            + rich_note(
                f"❍ ʙʏ » {user.mention}"
            ),
        )

    # ── NOOP ─────────────────────────────────────────────────────────────────

    elif data == "noop":
        await cbq.answer()

    # ── CLOSE HELP ──────────────────────────────────────────────────────────
    # Deletes the complete Help message.

    elif data == "close_help":

        await cbq.answer()

        try:
            await cbq.message.delete()
        except Exception:
            pass

    # ── SHOW HELP ────────────────────────────────────────────────────────────

    elif data == "show_help":

        await cbq.answer()

        photo = random.choice(
            config.START_PHOTOS
        )

        content = (
            rich_img(photo)
            + rich_note(
                "ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ "
                "ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴩ"
                "<br><br>"
                "ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ"
            )
        )

        if getattr(
            cbq.message,
            "photo",
            None,
        ):

            try:
                await cbq.message.delete()
            except Exception:
                pass

            await rich_send(
                bot,
                chat_id,
                content,
                reply_markup=_HELP_KB,
            )

        else:

            await rich_edit(
                cbq.message,
                content,
                reply_markup=_HELP_KB,
            )

    # ── CATEGORY HELP ────────────────────────────────────────────────────────

    elif data.startswith("help_"):

        await cbq.answer()

        photo = random.choice(
            config.START_PHOTOS
        )

        help_data = _HELP_TEXTS.get(data)

        if help_data:

            text = _category_html(
                help_data["title"],
                help_data["desc"],
                help_data["rows"],
                photo,
            )

            await rich_edit(
                cbq.message,
                text,
                reply_markup=_CLOSE_KB,
            )


# ── Legacy Go Back Function ──────────────────────────────────────────────────
# Kept unchanged so unrelated existing references do not break.

async def _go_back(cbq: CallbackQuery) -> None:

    await cbq.answer()

    uid = cbq.from_user.id
    name = sanitize_display_name(
        cbq.from_user.first_name
    )

    photo = random.choice(
        config.START_PHOTOS
    )

    caption = (
        rich_img(photo)
        + rich_note(
            f"<p>❍ ʜᴇʏ "
            f"<a href='tg://user?id={uid}'>"
            f"{rich_esc(name)}</a>, "
            "ᴡᴇʟᴄᴏᴍᴇ ᴀʙᴏᴀʀᴅ! 🎶</p>"
            + f"<p>ɪ ᴀᴍ "
            f"<b>{rich_esc(config.BOT_NAME)}</b> — "
            "ᴀ ғᴀsᴛ &amp; ᴘᴏᴡᴇʀғᴜʟ "
            "ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ "
            "ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ "
            "ғᴇᴀᴛᴜʀᴇs.</p>"
        )
        + rich_details(
            "✦ ᴋᴇʏ ғᴇᴀᴛᴜʀᴇs ✦",
            rich_table(
                [
                    "ғᴇᴀᴛᴜʀᴇ",
                    "ᴅᴇᴛᴀɪʟs",
                ],
                [
                    (
                        "🎵 s
