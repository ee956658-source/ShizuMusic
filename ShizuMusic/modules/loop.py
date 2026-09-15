# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
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
    # finite: N remaining additional plays
    if val > 0:
        new_val = val - 1
        set_loop(chat_id, new_val)
        return True
    return False


@bot.on_message(
    filters.group
    & filters.command("loop")
    & group_allowed
    & user_allowed
)
async def loop_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        await rich_send(
            bot,
            chat_id,
            rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
            + rich_note("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs."),
        )
        return

    if not queue_size(chat_id) or not peek_current(chat_id):
        await rich_send(
            bot,
            chat_id,
            rich_heading("❍ ɴᴏ ᴛʀᴀᴄᴋ ᴘʟᴀʏɪɴɢ", level=3)
            + rich_note("ʟᴏᴏᴘ ᴋᴇ ʟɪʏᴇ ᴋᴏɪ sᴏɴɢ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ."),
        )
        return

    args = (message.command[1:] if len(message.command) > 1 else [])
    arg = args[0].lower() if args else ""

    current = peek_current(chat_id)
    title = rich_esc(current.get("title", "Unknown") if current else "Unknown")

    # ── /loop  (no args) → show status ───────────────────────────────────────
    if not arg:
        val = get_loop(chat_id)
        if val == 0:
            status = "ᴅɪsᴀʙʟᴇᴅ"
        elif val == -1:
            status = "ᴇɴᴀʙʟᴇᴅ (ɪɴғɪɴɪᴛᴇ)"
        else:
            status = f"ᴇɴᴀʙʟᴇᴅ ({val} ʀᴇᴍᴀɪɴɪɴɢ)"
        await rich_send(
            bot,
            chat_id,
            rich_heading("🔁 ʟᴏᴏᴘ sᴛᴀᴛᴜs", level=3)
            + rich_note(
                f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                f"sᴛᴀᴛᴜs: <b>{status}</b></p>"
                f"<p>/loop enable · /loop disable · /loop [1-10]</p>"
            ),
        )
        return

    # ── /loop enable ─────────────────────────────────────────────────────────
    if arg in ("enable", "on", "true", "yes"):
        set_loop(chat_id, -1)
        await rich_send(
            bot,
            chat_id,
            rich_heading("🔁 ʟᴏᴏᴘ ᴇɴᴀʙʟᴇᴅ", level=3)
            + rich_note(
                f"<p>sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ</p>"
                f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                f"ᴍᴏᴅᴇ: <b>ɪɴғɪɴɪᴛᴇ</b></p>"
            ),
        )
        return

    # ── /loop disable ────────────────────────────────────────────────────────
    if arg in ("disable", "off", "false", "no"):
        clear_loop(chat_id)
        await rich_send(
            bot,
            chat_id,
            rich_heading("🔁 ʟᴏᴏᴘ ᴅɪsᴀʙʟᴇᴅ", level=3)
            + rich_note(
                f"<p>ʟᴏᴏᴘ ᴛᴜʀɴᴇᴅ ᴏғғ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ</p>"
                f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code></p>"
            ),
        )
        return

    # ── /loop [1, 2, 3, ...] ──────────────────────────────────────────────────
    if arg.isdigit():
        n = int(arg)
        if n < 1:
            await rich_send(
                bot,
                chat_id,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴠᴀʟᴜᴇ", level=3)
                + rich_note("ʟᴏᴏᴘ ᴄᴏᴜɴᴛ 1 sᴇ 10 ᴛᴀᴋ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ."),
            )
            return
        if n > 10:
            n = 10  # safety cap
        set_loop(chat_id, n)
        await rich_send(
            bot,
            chat_id,
            rich_heading("🔁 ʟᴏᴏᴘ ᴇɴᴀʙʟᴇᴅ", level=3)
            + rich_note(
                f"<p>sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ</p>"
                f"<p>ᴛʀᴀᴄᴋ: <code>{title}</code><br>"
                f"ᴄᴏᴜɴᴛ: <b>{n}</b> ᴍᴏʀᴇ ᴛɪᴍᴇs</p>"
            ),
        )
        return

    await rich_send(
        bot,
        chat_id,
        rich_heading("❍ ᴜsᴀɢᴇ", level=3)
        + rich_note(
            "<p>/loop enable — ɪɴғɪɴɪᴛᴇ ʟᴏᴏᴘ<br>"
            "/loop disable — ᴛᴜʀɴ ᴏғғ<br>"
            "/loop [1-10] — ʟᴏᴏᴘ ɴ ᴛɪᴍᴇs</p>"
        ),
    )
