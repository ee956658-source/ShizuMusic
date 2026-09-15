# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import LOGGER, bot
from ShizuMusic.core.queue import peek_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import rich_esc, rich_heading, rich_note, rich_send


# chat_id -> loop remaining
#  0  = disabled
# -1  = infinite (enable)
#  N  = remaining additional plays after current ends
_loop: dict[int, int] = {}


def get_loop(chat_id: int) -> int:
    return _loop.get(chat_id, 0)


def set_loop(chat_id: int, value: int) -> None:
    if value == 0:
        _loop.pop(chat_id, None)
    else:
        _loop[chat_id] = value


def clear_loop(chat_id: int) -> None:
    _loop.pop(chat_id, None)


def is_looping(chat_id: int) -> bool:
    return get_loop(chat_id) != 0


def consume_loop(chat_id: int) -> bool:
    """
    Called when a track ends.
    Returns True if the same track should be replayed.
    Decrements finite loop count.
    """
    val = get_loop(chat_id)
    if val == 0:
        return False
    if val == -1:
        return True  # infinite
    if val > 0:
        set_loop(chat_id, val - 1)
        return True
    return False


async def _reply(chat_id: int, text: str, message: Message = None) -> None:
    """Always try to reply; fall back to plain text if rich UI fails."""
    try:
        await rich_send(bot, chat_id, text)
        return
    except Exception as e:
        LOGGER.warning(f"[Loop] rich_send failed: {e}")
    try:
        plain = (
            text.replace("<p>", "")
            .replace("</p>", "\n")
            .replace("<br>", "\n")
            .replace("<b>", "")
            .replace("</b>", "")
            .replace("<code>", "")
            .replace("</code>", "")
        )
        for tag in ("h1", "h2", "h3", "h4", "small"):
            plain = plain.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
        if message:
            await message.reply_text(plain.strip()[:4000])
        else:
            await bot.send_message(chat_id, plain.strip()[:4000])
    except Exception as e2:
        LOGGER.error(f"[Loop] plain reply failed: {e2}")


@bot.on_message(
    filters.group
    & filters.command(["loop"])
    & group_allowed
    & user_allowed
)
async def loop_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    LOGGER.info(
        f"[Loop] command received in {chat_id} from "
        f"{message.from_user.id if message.from_user else 0}: {message.text}"
    )

    try:
        if not await is_user_authorized(message):
            await _reply(
                chat_id,
                rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
                + rich_note("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs."),
                message,
            )
            return

        size = queue_size(chat_id)
        current = peek_current(chat_id)
        LOGGER.info(f"[Loop] queue_size={size} current={bool(current)}")

        if size == 0 or not current:
            await _reply(
                chat_id,
                rich_heading("❍ ɴᴏ ᴛʀᴀᴄᴋ ᴘʟᴀʏɪɴɢ", level=3)
                + rich_note("ʟᴏᴏᴘ ᴋᴇ ʟɪʏᴇ ᴋᴏɪ sᴏɴɢ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ."),
                message,
            )
            return

        args = message.command[1:] if len(message.command) > 1 else []
        arg = args[0].lower().strip() if args else ""
        title = rich_esc(str(current.get("title", "Unknown")))

        # ── /loop  (status) ──────────────────────────────────────────────────
        if not arg:
            val = get_loop(chat_id)
            if val == 0:
                status = "ᴅɪsᴀʙʟᴇᴅ"
            elif val == -1:
                status = "ᴇɴᴀʙʟᴇᴅ (ɪɴғɪɴɪᴛᴇ)"
            else:
                status = f"ᴇɴᴀʙʟᴇᴅ ({val} ʀᴇᴍᴀɪɴɪɴɢ)"
            await _reply(
                chat_id,
                rich_heading("🔁 ʟᴏᴏᴘ sᴛᴀᴛᴜs", level=3)
                + rich_note(
                    f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                    f"sᴛᴀᴛᴜs: <b>{status}</b></p>"
                    f"<p>/loop enable · /loop disable · /loop [1-10]</p>"
                ),
                message,
            )
            return

        # ── /loop enable ─────────────────────────────────────────────────────
        if arg in ("enable", "on", "true", "yes"):
            set_loop(chat_id, -1)
            await _reply(
                chat_id,
                rich_heading("🔁 ʟᴏᴏᴘ ᴇɴᴀʙʟᴇᴅ", level=3)
                + rich_note(
                    f"<p>sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ</p>"
                    f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                    f"ᴍᴏᴅᴇ: <b>ɪɴғɪɴɪᴛᴇ</b></p>"
                ),
                message,
            )
            return

        # ── /loop disable ────────────────────────────────────────────────────
        if arg in ("disable", "off", "false", "no"):
            clear_loop(chat_id)
            await _reply(
                chat_id,
                rich_heading("🔁 ʟᴏᴏᴘ ᴅɪsᴀʙʟᴇᴅ", level=3)
                + rich_note(
                    f"<p>ʟᴏᴏᴘ ᴛᴜʀɴᴇᴅ ᴏғғ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ</p>"
                    f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code></p>"
                ),
                message,
            )
            return

        # ── /loop [1, 2, 3, ...] ──────────────────────────────────────────────
        if arg.isdigit():
            n = int(arg)
            if n < 1:
                await _reply(
                    chat_id,
                    rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴠᴀʟᴜᴇ", level=3)
                    + rich_note("ʟᴏᴏᴘ ᴄᴏᴜɴᴛ 1 sᴇ 10 ᴛᴀᴋ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ."),
                    message,
                )
                return
            if n > 10:
                n = 10
            set_loop(chat_id, n)
            await _reply(
                chat_id,
                rich_heading("🔁 ʟᴏᴏᴘ ᴇɴᴀʙʟᴇᴅ", level=3)
                + rich_note(
                    f"<p>sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ</p>"
                    f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                    f"ᴄᴏᴜɴᴛ: <b>{n}</b> ᴍᴏʀᴇ ᴛɪᴍᴇs</p>"
                ),
                message,
            )
            return

        await _reply(
            chat_id,
            rich_heading("❍ ᴜsᴀɢᴇ", level=3)
            + rich_note(
                "<p>/loop enable — ɪɴғɪɴɪᴛᴇ ʟᴏᴏᴘ<br>"
                "/loop disable — ᴛᴜʀɴ ᴏғғ<br>"
                "/loop [1-10] — ʟᴏᴏᴘ ɴ ᴛɪᴍᴇs</p>"
            ),
            message,
        )

    except Exception as e:
        LOGGER.error(f"[Loop] handler error: {e}", exc_info=True)
        try:
            await message.reply_text(f"Loop error: {e}")
        except Exception:
            pass
