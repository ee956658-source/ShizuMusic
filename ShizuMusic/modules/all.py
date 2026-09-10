import asyncio

from pyrogram import filters, enums
from pyrogram.types import Message

from ShizuMusic import bot
import config


ALL_RUNNING = {}


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


@bot.on_message(
    filters.group & filters.command("all"),
    group=1
)
async def all_handler(_, message: Message):

    try:
        if not await is_admin(message):
            return

        if not message.text:
            return

        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            return

        text = parts[1].strip()

        if not text:
            return

        chat_id = message.chat.id
        ALL_RUNNING[chat_id] = True

        users = []

        async for member in bot.get_chat_members(chat_id):

            if not ALL_RUNNING.get(chat_id):
                return

            user = member.user

            if not user or user.is_deleted or user.is_bot:
                continue

            users.append(user)

        if not users:
            await message.reply_text("No members found.")
            return

        for i in range(0, len(users), 5):

            if not ALL_RUNNING.get(chat_id):
                break

            batch = users[i:i + 5]

            mentions = []

            for user in batch:
                name = user.first_name or "User"

                mentions.append(
                    f'<a href="tg://user?id={user.id}">{name}</a>'
                )

            await message.reply_text(
                f"{text}\n\n"
                + "\n\n".join(mentions)
                + "\n\n"
                + "<tg-spoiler>Use /alloff to stop</tg-spoiler>"
            )

            await asyncio.sleep(1)

    except Exception as e:
        await message.reply_text(f"ALL ERROR: {e}")

    finally:
        ALL_RUNNING.pop(message.chat.id, None)


@bot.on_message(
    filters.group & filters.command("alloff"),
    group=1
)
async def alloff_handler(_, message: Message):

    try:
        if await is_admin(message):
            ALL_RUNNING[message.chat.id] = False
    except Exception:
        return
