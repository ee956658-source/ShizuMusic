# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.utils.db import (
    save_filter,
    get_filter,
    delete_filter,
)


async def is_admin_or_owner(message: Message) -> bool:
    if not message.from_user:
        return False

    try:
        if message.from_user.id == bot.owner_id:
            return True
    except Exception:
        pass

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )

        return member.status in ("administrator", "owner")

    except Exception:
        return False


# ── Save Filter ────────────────────────────────────────────────────────────────

@bot.on_message(filters.group & filters.command("filter"))
async def add_filter(_, message: Message) -> None:
    if not message.reply_to_message:
        return

    if not await is_admin_or_owner(message):
        return

    if len(message.command) < 2:
        return

    name = message.command[1].strip().lower()

    if not name:
        return

    source = message.reply_to_message

    save_filter(
        message.chat.id,
        name,
        source.chat.id,
        source.id,
    )

    await message.reply_text("saved filter")


# ── Stop Filter ────────────────────────────────────────────────────────────────

@bot.on_message(filters.group & filters.command("stop"))
async def stop_filter(_, message: Message) -> None:
