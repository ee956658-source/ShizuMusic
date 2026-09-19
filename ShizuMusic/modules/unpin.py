from html import escape

from pyrogram import enums, filters
from pyrogram.types import Message

from ShizuMusic import bot


async def _can_pin(message: Message) -> bool:
    if not message.from_user:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status == enums.ChatMemberStatus.OWNER or bool(
            getattr(member.privileges, "can_pin_messages", False)
        )
    except Exception:
        return False


@bot.on_message(filters.group & filters.command("unpin"))
async def unpin_message(_, message: Message) -> None:
    if not await _can_pin(message):
        return await message.reply_text("❌ You need pin-message permission.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a pinned message with /unpin.")
    try:
        await bot.unpin_chat_message(message.chat.id, message.reply_to_message.id)
        await message.delete()
    except Exception as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)
