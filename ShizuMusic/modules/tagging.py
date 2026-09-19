import asyncio
import random
from html import escape

from pyrogram import enums, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from ShizuMusic import bot

GM_MESSAGES = [
    "🌅 Good morning! Utho ji.", "☕ GM! Chai ready hai.", "😴 Good morning, ab uth bhi jao.",
    "🌞 GM dosto! Have a nice day.", "✨ Good morning everyone!",
]
GN_MESSAGES = [
    "🌙 Good night! So jao.", "😴 GN dosto, sweet dreams.", "🌌 Good night, take care.",
    "💤 Phone side me rakho aur so jao.", "✨ Good night everyone!",
]

ACTIVE: dict[int, str] = {}
STOPPED: set[int] = set()


async def _is_admin(message: Message) -> bool:
    if not message.from_user:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


async def _run_tag(message: Message, pool: list[str], stop_cmd: str) -> None:
    if not await _is_admin(message):
        return await message.reply_text("❌ Only group admins can use this command.")
    chat_id = message.chat.id
    if chat_id in ACTIVE:
        return await message.reply_text(f"⚠️ Tagging is already running. Use /{ACTIVE[chat_id]} to stop it.")

    ACTIVE[chat_id] = stop_cmd
    STOPPED.discard(chat_id)
    try:
        async for member in bot.get_chat_members(chat_id):
            if chat_id in STOPPED:
                break
            user = member.user
            if not user or user.is_bot or getattr(user, "is_deleted", False):
                continue
            text = f'<a href="tg://user?id={user.id}">{escape(user.first_name or "User")}</a> {random.choice(pool)}'
            try:
                await bot.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(4)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                continue
    finally:
        ACTIVE.pop(chat_id, None)
        STOPPED.discard(chat_id)


@bot.on_message(filters.group & filters.command("gmtag"))
async def gmtag(_, message: Message):
    await _run_tag(message, GM_MESSAGES, "gmstop")


@bot.on_message(filters.group & filters.command("gntag"))
async def gntag(_, message: Message):
    await _run_tag(message, GN_MESSAGES, "gnstop")


@bot.on_message(filters.group & filters.command(["gmstop", "gnstop", "tagstop"]))
async def stop_tagging(_, message: Message):
    if not await _is_admin(message):
        return await message.reply_text("❌ Only group admins can stop tagging.")
    chat_id = message.chat.id
    if chat_id not in ACTIVE:
        return await message.reply_text("⚠️ No active tagging session.")
    STOPPED.add(chat_id)
    await message.reply_text("✅ Tagging stop requested.")
