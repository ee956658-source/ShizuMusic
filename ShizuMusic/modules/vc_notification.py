from html import escape

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message

from ShizuMusic import bot


async def _safe_reply(message: Message, text: str) -> None:
    """Reply to VC service messages without letting notification errors affect the bot."""
    try:
        if not message.chat or message.chat.type == ChatType.CHANNEL:
            return
        await message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        # VC notifications are auxiliary; never break other handlers if Telegram
        # refuses the reply or the service message cannot be replied to.
        return


@bot.on_message(filters.group & filters.video_chat_started)
async def voice_chat_started(_, message: Message):
    await _safe_reply(
        message,
        "🎙️ <b>VOICE CHAT HAS STARTED!</b>",
    )


@bot.on_message(filters.group & filters.video_chat_ended)
async def voice_chat_ended(_, message: Message):
    await _safe_reply(
        message,
        "🔕 <b>VOICE CHAT ENDED.</b>",
    )


@bot.on_message(filters.group & filters.video_chat_members_invited)
async def voice_chat_members_invited(_, message: Message):
    service = getattr(message, "video_chat_members_invited", None)
    users = getattr(service, "users", None) or []

    if not users:
        return

    if message.from_user:
        inviter_name = message.from_user.first_name or "Someone"
        inviter = (
            f'<a href="tg://user?id={message.from_user.id}">'
            f"{escape(inviter_name)}"
            "</a>"
        )
    else:
        inviter = "Someone"

    invited = []
    for user in users:
        try:
            name = escape(user.first_name or "User")
            invited.append(
                f'<a href="tg://user?id={user.id}">{name}</a>'
            )
        except Exception:
            continue

    if not invited:
        return

    await _safe_reply(
        message,
        f"👥 {inviter} <b>INVITED</b> {', '.join(invited)} "
        "TO THE VOICE CHAT. 😉",
    )
