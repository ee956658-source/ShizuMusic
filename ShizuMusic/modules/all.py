import asyncio

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot


ALL_RUNNING = {}


@bot.on_message(
    filters.group & filters.command("all"),
    group=1
)
async def all_handler(_, message: Message):

    if not message.from_user:
        return

    chat_id = message.chat.id

    # Only group admins and owner
    member = await bot.get_chat_member(
        chat_id,
        message.from_user.id
    )

    if member.status not in ("administrator", "owner"):
        return

    if not message.text:
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        return

    text = parts[1].strip()

    if not text:
        return

    ALL_RUNNING[chat_id] = True

    users = []

    async for member in bot.get_chat_members(chat_id):

        if not ALL_RUNNING.get(chat_id):
            return

        user = member.user

        if not user:
            continue

        if user.is_bot or user.is_deleted:
            continue

        users.append(user)

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
            + "\n".join(mentions)
            + "\n\n"
            + "<tg-spoiler>Use /alloff to stop</tg-spoiler>"
        )

        await asyncio.sleep(1)

    ALL_RUNNING.pop(chat_id, None)


@bot.on_message(
    filters.group & filters.command("alloff"),
    group=1
)
async def alloff_handler(_, message: Message):

    if not message.from_user:
        return

    member = await bot.get_chat_member(
        message.chat.id,
        message.from_user.id
    )

    if member.status not in ("administrator", "owner"):
        return

    ALL_RUNNING[message.chat.id] = False
