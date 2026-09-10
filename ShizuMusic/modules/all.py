from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot


@bot.on_message(
    filters.group & filters.command("all"),
    group=1
)
async def all_handler(_, message: Message):
    await message.reply_text("ALL WORKING")
