import asyncio

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, assistant
import config


# chat_id: True while /all is running
ALL_RUNNING = {}


def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID


async def is_admin(message: Message) -> bool:
    user = message.from_user

    if not user:
        return False

    if is_owner(user.id):
        return True

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            user.id
        )

        return member.status in (
            "administrator",
            "owner",
        )

    except Exception:
        return False


# ── /all ──────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("all") & filters.group)
async def all_handler(_, message: Message) -> None:

    if not await is_admin(message):
        return

    parts = message.text.split(maxsplit=1) if message.text else []

    if len(parts) < 2 or not parts[1].strip():
        return

    text = parts[1].strip()
    chat_id = message.chat.id

    ALL_RUNNING[chat_id] = True

    users = []

    try:
        async for member in assistant.get_chat_members(chat_id):

            if not ALL_RUNNING.get(chat_id):
                break

            user = member.user

            if not user:
                continue

            # Skip deleted accounts and bots
            if user.is_deleted or user.is_bot:
                continue

            # Skip the person who used /all
            if message.from_user and user.id == message.from_user.id:
                continue

            users.append(user)

    except Exception:
        ALL_RUNNING.pop(chat_id, None)
        return

    # 5 users per message
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

        reply = (
            f"{text}\n\n"
            + "\n".join(mentions)
            + "\n\n"
            + "<tg-spoiler>Use /alloff to stop</tg-spoiler>"
        )

        try:
            await message.reply_text(
                reply,
                disable_web_page_preview=True
            )
        except Exception:
            break

        await asyncio.sleep(1)

    ALL_RUNNING.pop(chat_id, None)


# ── /alloff ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("alloff") & filters.group)
async def alloff_handler(_, message: Message) -> None:

    if not await is_admin(message):
        return

    ALL_RUNNING[message.chat.id] = False
