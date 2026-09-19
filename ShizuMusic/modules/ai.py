# --------------------------------------------------------------------------------
# AI commands — Gemini + Groq fallback
# /ai <question> and /ask <question>
# NOTE: This file is isolated from the music/playback system.
# --------------------------------------------------------------------------------
import re

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, LOGGER
from ShizuMusic.utils.ai import ask_ai

_AI_COMMAND_RE = re.compile(r"^/(?:ai|ask)(?:@[A-Za-z0-9_]+)?(?:\s+(.*))?$", re.IGNORECASE | re.DOTALL)


def _get_prompt(message: Message) -> str:
    text = message.text or message.caption or ""
    match = _AI_COMMAND_RE.match(text.strip())
    if match and match.group(1):
        return match.group(1).strip()

    reply = message.reply_to_message
    if reply and reply.text:
        return reply.text.strip()
    if reply and reply.caption:
        return reply.caption.strip()
    return ""


async def ai_cmd(client, message: Message) -> None:
    LOGGER.info("========== AI COMMAND RECEIVED ==========")
    LOGGER.info("AI command text: %r", message.text or message.caption or "")

    prompt = _get_prompt(message)
    if not prompt:
        await message.reply_text(
            "✦ <b>AI Assistant</b>\n\n"
            "Use <code>/ai your question</code> or reply to a text with <code>/ai</code>."
        )
        return

    if len(prompt) > 12000:
        await message.reply_text("✦ Your prompt is too long. Please keep it under 12,000 characters.")
        return

    status = await message.reply_text("✦ <i>Thinking…</i>")
    try:
        answer, provider = await ask_ai(prompt)
        header = f"✦ <b>AI • {provider}</b>\n\n"
        chunks = [answer[i:i + 3900] for i in range(0, len(answer), 3900)] or [""]
        await status.delete()
        for i, chunk in enumerate(chunks):
            prefix = header if i == 0 else "✦ <b>AI</b>\n\n"
            try:
                await message.reply_text(prefix + chunk)
            except Exception:
                await message.reply_text(prefix + chunk, parse_mode=None)
    except Exception:
        LOGGER.exception("AI command failed")
        try:
            await status.edit_text(
                "✦ <b>AI unavailable</b>\n\n"
                "The AI provider request failed or no API key is configured.\n"
                "Check <code>GEMINI_API_KEY</code> / <code>GROQ_API_KEY</code>."
            )
        except Exception:
            pass


# Use a raw regex instead of filters.command so Telegram command parsing cannot
# prevent /ai or /ask from reaching this handler.
@bot.on_message(filters.regex(_AI_COMMAND_RE))
async def _ai_message_handler(client, message: Message) -> None:
    await ai_cmd(client, message)


LOGGER.info("========== AI HANDLER ACTIVE ==========")
