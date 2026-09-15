# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Loop command
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, LOGGER
from ShizuMusic.core.loop import is_loop, set_loop


@bot.on_message(
    filters.group & filters.command("loop", prefixes=["/"]),
    group=10,
)
async def loop_cmd(_, message: Message) -> None:
    """Enable, disable, or show the current-song loop state."""
    chat_id = int(message.chat.id)

    # Pyrogram parses /loop@BotUsername enable as ["loop", "enable"].
    args = list(getattr(message, "command", None) or [])
    action = args[1].lower() if len(args) > 1 else ""

    if action in ("enable", "on", "1"):
        set_loop(chat_id, True)
        text = "🔁 Loop enabled. The current song will repeat after it ends."
    elif action in ("disable", "off", "0"):
        set_loop(chat_id, False)
        text = "⏹ Loop disabled."
    else:
        status = "ON" if is_loop(chat_id) else "OFF"
        text = (
            "🔁 Loop usage:\n"
            "/loop enable — repeat the current song\n"
            "/loop disable — turn loop off\n\n"
            f"Current status: {status}"
        )

    try:
        await message.reply_text(text)
        LOGGER.info("Loop command handled in chat %s: %s", chat_id, action or "status")
    except Exception:
        LOGGER.exception("Loop command reply failed in chat %s", chat_id)
