# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, call_py
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import peek_current, pop_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import (
    rich_heading,
    rich_note,
    rich_send,
)


@bot.on_message(
    filters.group
    & filters.command("skip")
    & group_allowed
    & user_allowed
)
async def skip_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    # Owner / Admin / Authorized user
    if not await is_user_authorized(message):
        await rich_send(
            bot,
            chat_id,
            rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
            + rich_note("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs."),
        )
        return

    # Nothing currently playing
    if not queue_size(chat_id):
        return

    skipped = pop_current(chat_id)

    # Stop current voice call
    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass

    await asyncio.sleep(2)

    # Remove downloaded audio file
    try:
        delete_file(skipped.get("file_path", ""))
    except Exception:
        pass

    # Clickable Telegram name of the person who used /skip
    user = message.from_user

    if user:
        user_name = user.mention
    else:
        user_name = "Unknown"

    # Skip confirmation
    await rich_send(
        bot,
        chat_id,
        f"<p>⏭️ sᴛʀᴇᴀᴍ sᴋɪᴘᴘᴇᴅ ʙʏ {user_name}</p>",
    )

    # Start next queued song automatically
    nxt = peek_current(chat_id)

    if nxt:
        dm = await rich_send(
            bot,
            chat_id,
            rich_heading("❍ ʟᴏᴀᴅɪɴɢ...", level=3),
        )

        await play_song(chat_id, dm, nxt)
