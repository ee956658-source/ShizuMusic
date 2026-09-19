from html import escape

from pyrogram import enums, filters
from pyrogram.types import Message

from ShizuMusic import bot


@bot.on_message(filters.group & filters.command(["adminlist", "staff"]))
async def admin_list(_, message: Message) -> None:
    try:
        admins = []
        async for member in bot.get_chat_members(
            message.chat.id,
            filter=enums.ChatMembersFilter.ADMINISTRATORS,
        ):
            if member.status == enums.ChatMemberStatus.OWNER:
                admins.insert(0, ("owner", member.user))
            else:
                admins.append(("admin", member.user))

        lines = [f"🛡️ <b>Staff — {escape(message.chat.title or 'Group')}</b>\n"]
        for kind, user in admins:
            name = escape(user.first_name or "User")
            mention = f'<a href="tg://user?id={user.id}">{name}</a>'
            if user.username:
                mention += f" (@{escape(user.username)})"
            lines.append(f"{'👑' if kind == 'owner' else '👤'} {mention}")
        lines.append(f"\n<b>Total:</b> {len(admins)}")
        await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)
