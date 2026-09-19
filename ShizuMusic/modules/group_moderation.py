from html import escape
import asyncio

from pyrogram import enums, filters
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, RPCError
from pyrogram.types import ChatPermissions, Message

from ShizuMusic import bot
import config


def _is_admin(member) -> bool:
    return member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)


async def _caller_has(message: Message, privilege: str) -> bool:
    if not message.from_user:
        return False
    if message.from_user.id == config.OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status == enums.ChatMemberStatus.OWNER:
            return True
        return bool(getattr(member.privileges, privilege, False))
    except Exception:
        return False


async def _target(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        try:
            return await bot.get_users(message.command[1])
        except Exception:
            return None
    return None


async def _target_member(chat_id: int, user_id: int):
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return None


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{escape(user.first_name or "User")}</a>'


def _reason(message: Message) -> str:
    if message.reply_to_message:
        return " ".join(message.command[1:]).strip()
    return " ".join(message.command[2:]).strip()


@bot.on_message(filters.group & filters.command(["mute", "unmute"]))
async def mute_commands(_, message: Message) -> None:
    cmd = message.command[0].lower()
    if not await _caller_has(message, "can_restrict_members"):
        return await message.reply_text("❌ You need permission to restrict members.")

    user = await _target(message)
    if not user:
        return await message.reply_text(f"Usage: /{cmd} @user or reply to a user's message.")

    member = await _target_member(message.chat.id, user.id)
    if member and _is_admin(member):
        return await message.reply_text("❌ I can't change an administrator or the owner.")

    try:
        if cmd == "mute":
            await bot.restrict_chat_member(
                message.chat.id,
                user.id,
                ChatPermissions(can_send_messages=False),
            )
            text = f"🔇 {_mention(user)} <b>muted</b>."
        else:
            await bot.restrict_chat_member(
                message.chat.id,
                user.id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True,
                ),
            )
            text = f"🔊 {_mention(user)} <b>unmuted</b>."
        reason = _reason(message)
        if reason:
            text += f"\nReason: {escape(reason)}"
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    except (ChatAdminRequired, UserAdminInvalid) as e:
        await message.reply_text(f"❌ Telegram denied the action: {e}")
    except RPCError as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)


@bot.on_message(filters.group & filters.command("kick"))
async def kick_command(_, message: Message) -> None:
    if not await _caller_has(message, "can_restrict_members"):
        return await message.reply_text("❌ You need permission to restrict members.")
    user = await _target(message)
    if not user:
        return await message.reply_text("Usage: /kick @user or reply to a user's message.")
    member = await _target_member(message.chat.id, user.id)
    if member and _is_admin(member):
        return await message.reply_text("❌ I can't kick an administrator or the owner.")
    try:
        await bot.ban_chat_member(message.chat.id, user.id)
        await asyncio.sleep(2)
        await bot.unban_chat_member(message.chat.id, user.id)
        text = f"👢 {_mention(user)} <b>kicked</b>."
        reason = _reason(message)
        if reason:
            text += f"\nReason: {escape(reason)}"
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    except (ChatAdminRequired, UserAdminInvalid) as e:
        await message.reply_text(f"❌ Telegram denied the action: {e}")
    except RPCError as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)


@bot.on_message(filters.group & filters.command("kickme"))
async def kick_me(_, message: Message) -> None:
    if not message.from_user:
        return
    member = await _target_member(message.chat.id, message.from_user.id)
    if member and _is_admin(member):
        return await message.reply_text("😅 Admins can't kick themselves with this command.")
    bot_member = await _target_member(message.chat.id, (await bot.get_me()).id)
    if not bot_member or not getattr(bot_member.privileges, "can_restrict_members", False):
        return await message.reply_text("❌ I need restrict/ban permission to kick you.")
    try:
        await bot.ban_chat_member(message.chat.id, message.from_user.id)
        await asyncio.sleep(3)
        await bot.unban_chat_member(message.chat.id, message.from_user.id)
        await message.reply_text("👢 You have been kicked from the group.")
    except Exception as e:
        await message.reply_text(f"❌ Failed: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)
