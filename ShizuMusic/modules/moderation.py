from html import escape

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import ChatPermissions, Message

import config
from ShizuMusic import bot
from ShizuMusic.utils.db import (
    get_warns,
    add_warn,
    remove_warn,
    reset_warns,
)


async def is_admin_or_owner(message: Message) -> bool:
    if not message.from_user:
        return False

    if message.from_user.id == config.OWNER_ID:
        return True

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )
        return member.status in ("administrator", "owner")
    except Exception:
        return False


async def get_target(message: Message, command_args: list):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, command_args

    if not command_args:
        return None, []

    target_text = command_args[0]

    try:
        user = await bot.get_users(target_text)
        return user, command_args[1:]
    except Exception:
        return None, []


async def is_target_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "owner")
    except Exception:
        return False


def mention(user) -> str:
    name = escape(user.first_name or "User")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def get_reason(args: list) -> str:
    return " ".join(args).strip()


@bot.on_message(filters.group & filters.command("mute"))
async def mute_user(_, message: Message):
    if not await is_admin_or_owner(message):
        await message.reply_text("You need to be an admin to use this command")
        return

    target, args = await get_target(message, message.command[1:])

    if not target:
        return

    if await is_target_admin(message.chat.id, target.id):
        await message.reply_text("You can't mute an admin")
        return

    reason = get_reason(args)

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            target.id,
            ChatPermissions(can_send_messages=False),
        )
    except Exception:
        return

    admin = message.from_user

    text = f"{mention(target)} is muted by {mention(admin)}"

    if reason:
        text += f"\nReason - {escape(reason)}"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(filters.group & filters.command("unmute"))
async def unmute_user(_, message: Message):
    if not await is_admin_or_owner(message):
        await message.reply_text("You need to be an admin to use this command")
        return

    target, args = await get_target(message, message.command[1:])

    if not target:
        return

    if await is_target_admin(message.chat.id, target.id):
        await message.reply_text("You can't unmute an admin")
        return

    reason = get_reason(args)

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            target.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
    except Exception:
        return

    admin = message.from_user

    text = f"{mention(target)} is unmuted by {mention(admin)}"

    if reason:
        text += f"\nReason - {escape(reason)}"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(filters.group & filters.command("warn"))
async def warn_user(_, message: Message):
    if not await is_admin_or_owner(message):
        await message.reply_text("You need to be an admin to use this command")
        return

    target, args = await get_target(message, message.command[1:])

    if not target:
        return

    if await is_target_admin(message.chat.id, target.id):
        await message.reply_text("You can't warn an admin")
        return

    reason = get_reason(args)

    warns = add_warn(message.chat.id, target.id)

    if warns >= 3:
        try:
            await bot.ban_chat_member(
                message.chat.id,
                target.id,
            )
        except Exception:
            return

        reset_warns(message.chat.id, target.id)

        admin = message.from_user

        text = f"{mention(target)} was banned by {mention(admin)}"

        if reason:
            text += f"\nReason - {escape(reason)}"

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )
        return

    admin = message.from_user

    text = f"{mention(target)} is warned by {mention(admin)}"

    if reason:
        text += f"\nReason - {escape(reason)}"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(filters.group & filters.command("unwarn"))
async def unwarn_user(_, message: Message):
    if not await is_admin_or_owner(message):
        await message.reply_text("You need to be an admin to use this command")
        return

    target, args = await get_target(message, message.command[1:])

    if not target:
        return

    if await is_target_admin(message.chat.id, target.id):
        await message.reply_text("You can't unwarn an admin")
        return

    reason = get_reason(args)

    warns = remove_warn(message.chat.id, target.id)

    if warns < 0:
        return

    admin = message.from_user

    text = f"{mention(target)} warning removed by {mention(admin)}"

    if reason:
        text += f"\nReason - {escape(reason)}"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )
