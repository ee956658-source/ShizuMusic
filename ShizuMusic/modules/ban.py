from pyrogram import filters, enums
from pyrogram.types import Message

from ShizuMusic import bot
import config


async def is_admin(message: Message) -> bool:
    if not message.from_user:
        return False

    if message.from_user.id == config.OWNER_ID:
        return True

    member = await bot.get_chat_member(
        message.chat.id,
        message.from_user.id
    )

    return member.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    )


async def get_target_user(message: Message):
    # Reply se user
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    # ID / username se user
    if not message.text:
        return None

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        return None

    target = parts[1].strip()

    try:
        return await bot.get_users(target)
    except Exception:
        return None


def mention_user(user):
    name = user.first_name or "User"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


@bot.on_message(
    filters.group & filters.command("ban"),
    group=1
)
async def ban_handler(_, message: Message):

    # Normal member
    if not await is_admin(message):
        await message.reply_text(
            "you need to be admin to use this command"
        )
        return

    target = await get_target_user(message)

    if not target:
        return

    # Check target's group status
    try:
        target_member = await bot.get_chat_member(
            message.chat.id,
            target.id
        )
    except Exception:
        return

    # Don't ban admins
    if target_member.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        await message.reply_text(
            "I won't ban admin"
        )
        return

    # Don't ban deleted accounts
    if target.is_deleted:
        return

    try:
        await bot.ban_chat_member(
            message.chat.id,
            target.id
        )

        await message.reply_text(
            f"{mention_user(target)} was banned by "
            f"{mention_user(message.from_user)}"
        )

    except Exception:
        return


@bot.on_message(
    filters.group & filters.command("unban"),
    group=1
)
async def unban_handler(_, message: Message):

    # Normal member
    if not await is_admin(message):
        await message.reply_text(
            "you need to be admin to use this command"
        )
        return

    target = await get_target_user(message)

    if not target:
        return

    try:
        await bot.unban_chat_member(
            message.chat.id,
            target.id
        )

        await message.reply_text(
            f"{mention_user(target)} was unbanned by "
            f"{mention_user(message.from_user)}"
        )

    except Exception:
        return
