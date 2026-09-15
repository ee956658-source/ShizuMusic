# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, call_py
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import rich_esc, rich_heading, rich_note, rich_send


@bot.on_message(
    filters.group
    & filters.command("pause")
    & group_allowed
    & user_allowed
)
async def pause_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
            + rich_note("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs."),
        )
        return

    try:
        await call_py.pause(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading("⏸ sᴛʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ", level=3)
            + rich_note("ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ sᴛᴏᴘᴘᴇᴅ."),
        )
    except Exception as e:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘᴀᴜsᴇ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )



# ── /loop ─────────────────────────────────────────────────────────────────────

from pyrogram.enums import ParseMode
from ShizuMusic.core.loop_state import clear_loop, get_loop, set_loop
from ShizuMusic.core.queue import peek_current, queue_size


@bot.on_message(
    filters.group
    & filters.command(["loop"])
    & group_allowed
    & user_allowed
)
async def loop_cmd(_, message: Message) -> None:

    chat_id = message.chat.id
    user = message.from_user
    by = user.mention if user else "Unknown"

    async def _small(text: str) -> None:
        """Tidal/Olivia style — plain small message bubble, no rich card."""
        try:
            await message.reply_text(text, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            except Exception:
                pass

    try:
        if not await is_user_authorized(message):
            await _small("⛔ <b>Admin only</b>")
            return

        if not queue_size(chat_id) or not peek_current(chat_id):
            await _small("❍ No track playing")
            return

        args = message.command[1:] if len(message.command) > 1 else []
        arg = args[0].lower().strip() if args else ""

        if not arg:
            val = get_loop(chat_id)
            if val == 0:
                await _small("🔁 Loop is <b>disabled</b>")
            elif val == -1:
                await _small("🔁 Loop enabled (<b>infinite</b>)")
            else:
                await _small(f"🔁 Loop enabled (<b>{val}</b> times)")
            return

        if arg in ("enable", "on", "true", "yes"):
            set_loop(chat_id, -1)
            await _small(f"» <b>LOOP ENABLED</b> for enable times by : {by}")
            return

        if arg in ("disable", "off", "false", "no"):
            clear_loop(chat_id)
            await _small(f"» <b>LOOP DISABLED</b> by : {by}")
            return

        if arg.isdigit():
            n = int(arg)
            if n < 1:
                await _small("❍ Invalid (use 1–10)")
                return
            if n > 10:
                n = 10
            set_loop(chat_id, n)
            await _small(f"» <b>LOOP ENABLED</b> for <b>{n}</b> times by : {by}")
            return

        await _small("❍ /loop enable | disable | 1-10")

    except Exception as e:
        try:
            await message.reply_text(f"Loop error: {e}")
        except Exception:
            pass
