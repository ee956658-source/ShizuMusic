from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.utils.db import (
    save_filter,
    get_filter,
    delete_filter,
)

import config


async def is_admin_or_owner(message: Message) -> bool:
    if not message.from_user:
        return False

    # Owner check from config
    try:
        owner_id = getattr(config, "OWNER_ID", None)
        owner_ids = getattr(config, "OWNER_IDS", None)

        if owner_id and message.from_user.id == owner_id:
            return True
        if owner_ids and message.from_user.id in owner_ids:
            return True
    except Exception:
        pass

    # Admin / Creator check from chat
    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )
        return member.status in ("administrator", "creator", "owner")
    except Exception:
        return False


@bot.on_message(
    filters.group & filters.command("filter"),
    group=7
)
async def add_filter(_, message: Message) -> None:
    if not await is_admin_or_owner(message):
        return

    if not message.reply_to_message:
        await message.reply_text("Reply to a message and use /filter <name>")
        return

    if len(message.command) < 2:
        await message.reply_text("Use /filter <name>")
        return

    name = message.command[1].strip().lower()

    save_filter(
        message.chat.id,
        name,
        message.reply_to_message.chat.id,
        message.reply_to_message.id,
    )

    await message.reply_text("✅ Filter saved")


@bot.on_message(
    filters.group & filters.command("stop"),
    group=7
)
async def stop_filter(_, message: Message) -> None:
    if not await is_admin_or_owner(message):
        return

    if len(message.command) < 2:
        await message.reply_text("Use /stop <name>")
        return

    name = message.command[1].strip().lower()

    delete_filter(message.chat.id, name)

    await message.reply_text("🗑️ Filter removed")


@bot.on_message(
    filters.group
    & filters.text
    & ~filters.command(["filter", "stop"]),
    group=99
)
async def trigger_filter(_, message: Message) -> None:
    if not message.text:
        return

    name = message.text.strip().lower()
    if not name:
        return

    data = get_filter(message.chat.id, name)
    if not data:
        return

    try:
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=data["source_chat_id"],
            message_id=data["source_message_id"],
            reply_to_message_id=message.id,
        )
    except Exception:
        return
