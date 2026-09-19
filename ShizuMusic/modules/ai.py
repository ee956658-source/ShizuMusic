# --------------------------------------------------------------------------------
# AI commands — Gemini + Groq fallback
# /ai <question> and /ask <question>
# --------------------------------------------------------------------------------
from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, LOGGER
from ShizuMusic.utils.ai import ask_ai


def _get_prompt(message: Message) -> str:
    # Normal command: /ai hello world
    args = message.command[1:] if message.command else []
    if args:
        return " ".join(args).strip()

    # Reply to a text and send only /ai
    reply = message.reply_to_message
    if reply and reply.text:
        return reply.text.strip()
    if reply and reply.caption:
        return reply.caption.strip()
    return ""


@bot.on_message(filters.command(["ai", "ask"]))
async def ai_cmd(client, message: Message) -> None:
    # Keep this log deliberately before every other AI operation so Railway
    # immediately tells us whether Telegram updates are reaching this handler.
    LOGGER.info("AI COMMAND RECEIVED: %r", message.text or message.caption or "")

    prompt = _get_prompt(message)
    if not prompt:
        await message.reply_text(
            "✦ <b>AI Assistant</b>\n\n"
            "Use <code>/ai your question</code> or reply to a text with <code>/ai</code>."
        )
        return

    if len(prompt) > 12000:
        await message.reply_text(
            "✦ Your prompt is too long. Please keep it under 12,000 characters."
        )
        return

    status = await message.reply_text("✦ <i>Thinking…</i>")
    try:
        answer, provider = await ask_ai(prompt)
        LOGGER.info("AI RESPONSE SUCCESS: provider=%s", provider)

        header = f"✦ <b>AI • {provider}</b>\n\n"
        chunks = [answer[i:i + 3900] for i in range(0, len(answer), 3900)] or [""]

        await status.delete()
        for i, chunk in enumerate(chunks):
            prefix = header if i == 0 else "✦ <b>AI</b>\n\n"
            try:
                await message.reply_text(prefix + chunk)
            except Exception:
                # Fallback if an AI response contains unsupported Telegram HTML.
                await message.reply_text(prefix + chunk, parse_mode=None)

    except Exception as exc:
        LOGGER.exception("AI COMMAND FAILED: %s", exc)
        try:
            await status.edit_text(
                "✦ <b>AI unavailable</b>\n\n"
                "The AI provider request failed or no API key is configured.\n"
                "Check <code>GEMINI_API_KEY</code> / <code>GROQ_API_KEY</code>."
            )
        except Exception:
            pass
