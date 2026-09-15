# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Loop command
# --------------------------------------------------------------------------------

import re

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.loop import is_loop, set_loop


_LOOP_RE = re.compile(
    r"^/loop(?:@[A-Za-z0-9_]+)?(?:\s+(enable|disable|on|off|1|0))?\s*$",
    re.IGNORECASE,
)


async def loop_cmd(_, message: Message) -> None:
    """Enable/disable repeating of the current song."""
    text = (message.text or message.caption or "").strip()
    match = _LOOP_RE.fullmatch(text)
    if not match or not message.chat:
        return

    chat_id = int(message.chat.id)
    action = (match.group(1) or "").lower()

    if action in ("enable", "on", "1"):
        set_loop(chat_id, True)
        reply = "🔁 Loop enabled. Current song will repeat after it ends."
    elif action in ("disable", "off", "0"):
        set_loop(chat_id, False)
        reply = "⏹ Loop disabled."
    else:
        status = "ON" if is_loop(chat_id) else "OFF"
        reply = (
            "🔁 Loop usage:\n"
            "/loop enable - repeat current song\n"
            "/loop disable - turn loop off\n\n"
            f"Current status: {status}"
        )

    try:
        await message.reply_text(reply)
    except Exception as e:
        # Keep failures visible in the bot log instead of silently swallowing them.
        from ShizuMusic import LOGGER
        LOGGER.error(f"Loop command reply error in chat {chat_id}: {e}")


# Register a normal text handler and parse the command ourselves. This avoids
# Pyrogram command-filter/entity differences for /loop and /loop@BotUsername.
bot.add_handler(
    MessageHandler(
        loop_cmd,
        filters=filters.group & filters.text,
    ),
    group=0,
)
