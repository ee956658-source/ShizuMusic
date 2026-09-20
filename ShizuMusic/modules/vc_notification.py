from html import escape

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message

from ShizuMusic import bot


async def _safe_reply(message: Message, text: str) -> None:
    try:
        if not message.chat or message.chat.type == ChatType.CHANNEL:
            return

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@bot.on_message(filters.video_chat_started & filters.group)
async def on_voice_chat_started(_, message: Message):
    await _safe_reply(
        message,
        "🎙️ <b>VOICE CHAT HAS STARTED!</b>",
    )


@bot.on_message(filters.video_chat_ended & filters.group)
async def on_voice_chat_ended(_, message: Message):
    await _safe_reply(
        message,
        "🔕 <b>VOICE CHAT ENDED.</b>",
    )


@bot.on_message(filters.video_chat_members_invited & filters.group)
async def on_voice_chat_members_invited(_, message: Message):
    inviter = "Someone"

    if message.from_user:
        name = escape(message.from_user.first_name or "Someone")
        inviter = (
            f'<a href="tg://user?id={message.from_user.id}">'
            f"{name}</a>"
        )

    vcmi = getattr(message, "video_chat_members_invited", None)
    users = getattr(vcmi, "users", None) or []

    invited = []

    for user in users:
        try:
            name = escape(user.first_name or "User")
            invited.append(
                f'<a href="tg://user?id={user.id}">{name}</a>'
            )
        except Exception:
            continue

    if invited:
        await _safe_reply(
            message,
            f"👥 {inviter} <b>INVITED</b> "
            f"{', '.join(invited)} TO THE VOICE CHAT. 😉",
        )
