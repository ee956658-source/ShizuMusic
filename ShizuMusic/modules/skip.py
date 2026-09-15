# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShizuMusic import bot, call_py
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import peek_current, pop_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import rich_esc, rich_heading, rich_note, rich_send


@bot.on_message(
    filters.group
    & filters.command("skip")
    & group_allowed
    & user_allowed
)
async def skip_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        return

    if not queue_size(chat_id):
        return

    # Disable loop when skipping so the next track is not forced into loop
    try:
        from ShizuMusic.modules.loop import clear_loop
        clear_loop(chat_id)
    except Exception:
        pass

    skipped = pop_current(chat_id)

    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass

    await asyncio.sleep(1)

    try:
        delete_file(skipped.get("file_path", ""))
    except Exception:
        pass

    nxt = peek_current(chat_id)
    user = message.from_user
    user_name = user.first_name if user else "Unknown"
    user_display = user.mention if user else rich_esc(user_name)
    group_name = rich_esc(message.chat.title or "this group")

    if nxt:
        text = (
            rich_heading("Yor × Music 🎧", level=3)
            + rich_note(
                f"<p>⏭️ <b>STREAM SKIPPED BY</b> {user_display}</p>"
            )
        )
    else:
        text = (
            rich_heading("Yor × Music 🎧", level=3)
            + rich_note(
                f"<p>⏭️ <b>STREAM SKIPPED BY</b> {user_display}</p>"
                f"<p>⊙ <b>No more queued tracks in {group_name}, leaving videochat.</b></p>"
            )
        )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Close", callback_data="close_player")],
    ])

    await bot.send_message(
        chat_id,
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
        reply_to_message_id=message.id,
    )

    if nxt:
        dm = await rich_send(
            bot,
            chat_id,
            rich_heading("⏭ ɴᴇxᴛ ᴛʀᴀᴄᴋ", level=3),
        )
        await play_song(chat_id, dm, nxt)

