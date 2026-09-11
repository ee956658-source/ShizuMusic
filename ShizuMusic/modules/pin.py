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
import config


async def is_admin_or_owner(message: Message) -> bool:
    if not message.from_user:
        return False

    if message.from_user.id == config.OWNER_ID:
        return True

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )

        return member.status in ("administrator", "owner")

    except Exception:
        return False


@bot.on_message(filters.group & filters.command("pin"))
async def pin_message(_, message: Message) -> None:
    if not message.reply_to_message:
        return

    if not await is_admin_or_owner(message):
        return

    try:
        await bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.id,
        )
    except Exception:
        return

    try:
        await message.delete()
    except Exception:
        pass
