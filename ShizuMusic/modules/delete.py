# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

import config
from ShizuMusic import bot


def is_owner(user_id: int) -> bool:
    if user_id == getattr(config, "OWNER_ID", 0):
        return True

    owner_ids = getattr(config, "OWNER_IDS", [])
    return user_id in owner_ids


@bot.on_message(
    filters.group & filters.command("del")
)
async def delete_message(_, message: Message) -> None:

    # /del must be used as a reply
    if not message.reply_to_message:
        return

    # Check admin permission
    try:
        if not is_owner(message.from_user.id):
            member = await bot.get_chat_member(
                message.chat.id,
                message.from_user.id,
            )

            if member.status not in (
                "administrator",
                "owner",
            ):
                return

    except Exception:
        return

    # Delete replied message
    try:
        await bot.delete_messages(
            chat_id=message.chat.id,
            message_ids=message.reply_to_message.id,
        )
    except Exception:
        return

    # Delete /del command
    try:
        await bot.delete_messages(
            chat_id=message.chat.id,
            message_ids=message.id,
        )
    except Exception:
        pass
