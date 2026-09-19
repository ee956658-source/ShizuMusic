# --------------------------------------------------------------------------------
# AI commands — Gemini + Groq fallback
# /ai <question> and /ask <question>
# --------------------------------------------------------------------------------
import asyncio
import config
from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, LOGGER
from ShizuMusic.modules.block import is_user_blocked_db
from ShizuMusic.utils.ai import ask_ai

def _get_prompt(message: Message) -> str:
    args = message.command[1:] if message.command else []
    if args:
        return " ".join(args).strip()
    reply = message.reply_to_message
    if reply and reply.text:
        return reply.text.strip()
    if reply and reply.caption:
        return reply.caption.strip()
    return ""

@bot.on_message(filters.command(["ai", "ask"]))
async def ai_cmd(client, message: Message) -> None:
    # Keep the command filter independent from the optional blocked-user filter.
    # This makes /ai reachable even if the custom DB filter is unavailable.
    try:
        if message.from_user and is_user_blocked_db(message.from_user.id):
            return
    except Exception:
        # Never let the block-check prevent the AI command from being handled.
        pass

    LOGGER.info("AI command received from user=%s chat=%s",
                getattr(message.from_user, "id", None),
                getattr(message.chat, "id", None))
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
        # Telegram messages have a practical size limit; split long answers safely.
        header = f"✦ <b>AI • {provider}</b>\n\n"
        chunks = [answer[i:i + 3900] for i in range(0, len(answer), 3900)] or [""]
        await status.delete()
        for i, chunk in enumerate(chunks):
            prefix = header if i == 0 else "✦ <b>AI</b>\n\n"
            try:
                await message.reply_text(prefix + chunk)
            except Exception:
                # Fallback for AI text containing unsupported Telegram HTML.
                await message.reply_text(prefix + chunk, parse_mode=None)
    except Exception as exc:
        LOGGER.exception("AI command failed")
        try:
            await status.edit_text(
                "✦ <b>AI unavailable</b>\n\n"
                "Both configured AI providers failed or no API key is set.\n"
                "<i>Check GEMINI_API_KEY / GROQ_API_KEY and try again.</i>"
            )
        except Exception:
            pass
