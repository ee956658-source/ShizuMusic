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
from ShizuMusic.modules.block import group_allowed, user_allowed


@bot.on_message(
    filters.group
    & filters.command("del")
    & group_allowed
    & user_allowed
)
async def delete_message(_, message: Message) -> None:
    # Must be a reply to another message.
    if not message.reply_to_message:
        return

    # Only actual Telegram group admins can use /del.
    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )

        if member.status not in ("administrator", "owner"):
            return

    except Exception:
        return

    # Delete the replied message.
    try:
        await message.reply_to_message.delete()
    except Exception:
        return

    # Delete the /del command itself.
    try:
        await message.delete()
    except Exception:
        pass
