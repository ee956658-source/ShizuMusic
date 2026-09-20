from html import escape

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode

from ShizuMusic import bot


async def safe_reply(message, text):
    try:
        if not message.chat:
            return

        if message.chat.type == ChatType.CHANNEL:
            return

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@bot.on_message(filters.group)
async def voice_chat_notifications(_, message):
    # Voice Chat started
    if getattr(message, "video_chat_started", None):
        await safe_reply(
            message,
            "🎙️ <b>VOICE CHAT HAS STARTED!</b>",
        )
        return

    # Voice Chat ended
    if getattr(message, "video_chat_ended", None):
        await safe_reply(
            message,
            "🔕 <b>VOICE CHAT ENDED.</b>",
        )
        return

    # Users invited to Voice Chat
    invited_info = getattr(
        message,
        "video_chat_members_invited",
        None,
    )

    if invited_info:
        inviter = "Someone"

        if message.from_user:
            name = escape(
                message.from_user.first_name or "Someone"
            )
            inviter = (
                f'<a href="tg://user?id={message.from_user.id}">'
                f"{name}</a>"
            )

        users = getattr(invited_info, "users", None) or []
        invited = []

        for user in users:
            try:
                name = escape(user.first_name or "User")
                invited.append(
                    f'<a href="tg://user?id={user.id}">'
                    f"{name}</a>"
                )
            except Exception:
                continue

        if invited:
            await safe_reply(
                message,
                f"👥 {inviter} <b>INVITED</b> "
                f"{', '.join(invited)} "
                f"TO THE VOICE CHAT. 😉",
            )
