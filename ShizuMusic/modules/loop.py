# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Loop command
# --------------------------------------------------------------------------------

import re

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.loop import is_loop, set_loop


# Handle both /loop enable and /loop@BotUsername enable explicitly.
# This handler intentionally has no unrelated group/user middleware so the
# command cannot silently disappear before reaching the loop code.
@bot.on_message(
    filters.group
    & filters.regex(r"^/loop(?:@[A-Za-z0-9_]+)?(?:\s+(?:enable|disable|on|off|1|0))?\s*$", flags=re.IGNORECASE)
)
async def loop_cmd(_, message: Message) -> None:
    chat_id = int(message.chat.id)
    text = (message.text or message.caption or "").strip()
    parts = text.split()
    action = parts[1].lower() if len(parts) > 1 else ""

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
        await bot.send_message(
            chat_id,
            reply,
            reply_to_message_id=message.id,
        )
    except Exception:
        # Fallback for clients/configurations where replying is unavailable.
        await message.reply_text(reply)
