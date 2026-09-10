import asyncio

from pyrogram import filters, enums
from pyrogram.types import Message

from ShizuMusic import bot
import config


ALL_RUNNING = {}


async def is_admin(message: Message) -> bool:
    user = message.from_user

    if not user:
        return False

    # Owner can always use /all and /alloff
    if user.id == config.OWNER_ID:
        return True

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            user.id
        )

        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )

    except Exception as e:
        print(f"ALL ADMIN CHECK ERROR: {e}")
        return False


# ── /all ──────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group & filters.command("all"),
    group=1
)
async def all_handler(_, message: Message) -> None:

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

    try:
        async for member in bot.get_chat_members(chat_id):

            if not ALL_RUNNING.get(chat_id):
                break

            user = member.user

            if not user:
                continue

            if user.is_deleted:
                continue

            if user.is_bot:
                continue

            users.append(user)

    except Exception as e:
        ALL_RUNNING.pop(chat_id, None)

        await message.reply_text(
            f"ALL ERROR: {e}"
        )

        return

    if not users:
        ALL_RUNNING.pop(chat_id, None)
        return

    # 5 members per message
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

        except Exception as e:
            print(f"ALL SEND ERROR: {e}")
            break

        await asyncio.sleep(1)

    ALL_RUNNING.pop(chat_id, None)


# ── /alloff ───────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group & filters.command("alloff"),
    group=1
)
async def alloff_handler(_, message: Message) -> None:

    if not await is_admin(message):
        return

    ALL_RUNNING[message.chat.id] = False
