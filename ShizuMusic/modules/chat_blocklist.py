from html import escape

from pyrogram import filters
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.utils.db import block_group, unblock_group, is_group_blocked, get_blocked_groups


@bot.on_message(filters.command("blchat") & filters.user(config.OWNER_ID))
async def blchat(_, message: Message) -> None:
    if len(message.command) != 2:
        return await message.reply_text("Usage: /blchat -100xxxxxxxxxx")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Invalid chat ID.")
    if is_group_blocked(chat_id):
        return await message.reply_text("⚠️ Chat is already blocked.")
    block_group(chat_id)
    try:
        await bot.leave_chat(chat_id)
    except Exception:
        pass
    await message.reply_text(f"✅ Chat blocked: <code>{chat_id}</code>", parse_mode="html")


@bot.on_message(filters.command(["unblchat", "unblacklistchat", "whitelistchat"]) & filters.user(config.OWNER_ID))
async def unblchat(_, message: Message) -> None:
    if len(message.command) != 2:
        return await message.reply_text("Usage: /unblchat -100xxxxxxxxxx")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Invalid chat ID.")
    if not is_group_blocked(chat_id):
        return await message.reply_text("⚠️ Chat is not blocked.")
    unblock_group(chat_id)
    await message.reply_text(f"✅ Chat unblocked: <code>{chat_id}</code>", parse_mode="html")


@bot.on_message(filters.command(["blchats", "blacklistedchats"]) & filters.user(config.OWNER_ID))
async def blchats(_, message: Message) -> None:
    chats = get_blocked_groups()
    if not chats:
        return await message.reply_text("✅ No blocked chats.")
    text = "🚫 <b>Blocked Chats</b>\n\n" + "\n".join(
        f"{i}. <code>{escape(str(cid))}</code>" for i, cid in enumerate(chats, 1)
    )
    await message.reply_text(text, parse_mode="html")
