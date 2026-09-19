from html import escape

from pyrogram import enums, filters
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, RPCError
from pyrogram.types import ChatPrivileges, Message

from ShizuMusic import bot


async def _has_promote(message: Message) -> bool:
    if not message.from_user:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status == enums.ChatMemberStatus.OWNER or bool(
            getattr(member.privileges, "can_promote_members", False)
        )
    except Exception:
        return False


async def _user(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        try:
            return await bot.get_users(message.command[1])
        except Exception:
            return None
    return None


def _mention(user):
    return f'<a href="tg://user?id={user.id}">{escape(user.first_name or "User")}</a>'


LIMITED = ChatPrivileges(
    can_manage_chat=True,
    can_delete_messages=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_restrict_members=False,
    can_promote_members=False,
    can_change_info=False,
    is_anonymous=False,
)

FULL = ChatPrivileges(
    can_manage_chat=True,
    can_change_info=True,
    can_delete_messages=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_restrict_members=True,
    can_promote_members=True,
    can_manage_video_chats=True,
    is_anonymous=False,
)

NONE = ChatPrivileges(
    can_manage_chat=False,
    can_change_info=False,
    can_delete_messages=False,
    can_invite_users=False,
    can_pin_messages=False,
    can_restrict_members=False,
    can_promote_members=False,
    can_manage_video_chats=False,
    is_anonymous=False,
)


@bot.on_message(filters.group & filters.command(["promote", "demote"]))
async def promote_demote(_, message: Message) -> None:
    if not await _has_promote(message):
        return await message.reply_text("❌ You need promote-members permission.")
    cmd = message.command[0].lower()
    user = await _user(message)
    if not user:
        return await message.reply_text(f"Usage: /{cmd} @user or reply to a user.")

    member = await bot.get_chat_member(message.chat.id, user.id)
    if cmd == "promote" and member.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR):
        return await message.reply_text("❌ User is already an administrator.")
    if cmd == "demote" and member.status != enums.ChatMemberStatus.ADMINISTRATOR:
        return await message.reply_text("❌ User is not an administrator.")
    if cmd == "demote" and member.status == enums.ChatMemberStatus.OWNER:
        return await message.reply_text("❌ The group owner cannot be demoted.")

    try:
        await bot.promote_chat_member(
            message.chat.id,
            user.id,
            privileges=LIMITED if cmd == "promote" else NONE,
        )
        title = " ".join(message.command[2:]).strip() if cmd == "promote" else ""
        if cmd == "promote" and title:
            try:
                await bot.set_administrator_title(message.chat.id, user.id, title[:16])
            except Exception:
                pass
        action = "promoted" if cmd == "promote" else "demoted"
        await message.reply_text(
            f"✅ {_mention(user)} <b>{action}</b>." + (f"\nTitle: {escape(title[:16])}" if title else ""),
            parse_mode=enums.ParseMode.HTML,
        )
    except (ChatAdminRequired, UserAdminInvalid, RPCError) as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)
