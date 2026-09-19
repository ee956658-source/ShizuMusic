from html import escape

from pyrogram import enums, filters
from pyrogram.types import Message

from ShizuMusic import bot


async def _resolve(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        try:
            return await bot.get_users(message.command[1])
        except Exception:
            return None
    return message.from_user


@bot.on_message(filters.command(["userinfo", "whois", "info"]))
async def user_info(_, message: Message) -> None:
    user = await _resolve(message)
    if not user:
        return await message.reply_text("❌ User not found.")

    status = "Unknown"
    custom_title = None
    try:
        member = await bot.get_chat_member(message.chat.id, user.id)
        status = str(member.status).split(".")[-1].lower()
        custom_title = getattr(member, "custom_title", None)
    except Exception:
        pass

    name = escape(" ".join(x for x in [user.first_name, user.last_name] if x))
    username = f"@{escape(user.username)}" if user.username else "N/A"
    bio = "N/A"
    try:
        full = await bot.get_chat(user.id)
        bio = escape(getattr(full, "bio", None) or "N/A")
    except Exception:
        pass

    text = (
        "👤 <b>User Information</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Name:</b> {name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🏷️ <b>Group status:</b> {escape(status)}\n"
        f"⭐ <b>Premium:</b> {'Yes' if getattr(user, 'is_premium', False) else 'No'}\n"
        f"🤖 <b>Bot:</b> {'Yes' if user.is_bot else 'No'}\n"
        f"✅ <b>Verified:</b> {'Yes' if getattr(user, 'is_verified', False) else 'No'}\n"
        f"⚠️ <b>Scam:</b> {'Yes' if getattr(user, 'is_scam', False) else 'No'}\n"
        f"🎭 <b>Fake:</b> {'Yes' if getattr(user, 'is_fake', False) else 'No'}\n"
        f"💬 <b>Bio:</b> {bio}"
    )
    if custom_title:
        text += f"\n🎖️ <b>Admin title:</b> {escape(custom_title)}"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
