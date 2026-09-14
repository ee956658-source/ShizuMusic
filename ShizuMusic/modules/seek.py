# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShizuMusic import bot, call_py, LOGGER
from ShizuMusic.core.queue import peek_current
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.formatters import fmt_time, parse_dur, progress_bar, short
from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.youtube import resolve_stream

# ── Seek state tracker ─────────────────────────────────────────────────────────
_seek_state: dict[int, dict] = {}


def set_seek_state(chat_id: int, offset: int) -> None:
    _seek_state[chat_id] = {"start_ts": time.time(), "offset": offset}


def get_current_position(chat_id: int) -> int:
    state = _seek_state.get(chat_id)
    if not state:
        return 0
    return state["offset"] + int(time.time() - state["start_ts"])


def clear_seek_state(chat_id: int) -> None:
    _seek_state.pop(chat_id, None)


# ── Internal seek ──────────────────────────────────────────────────────────────

async def _seek_to(chat_id: int, target_sec: int, message: Message) -> None:
    from pytgcalls.types import AudioQuality, MediaStream

    song = peek_current(chat_id)
    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ ʀɪɢʜᴛ ɴᴏᴡ", level=3))
        return

    total_sec  = parse_dur(song.get("duration", "0:00"))
    target_sec = max(0, min(target_sec, total_sec - 1))

    pm = await rich_send(
        bot,
        chat_id,
        rich_heading("˹𝙔𝙤𝙧 ✘ 𝙈𝙪𝙨𝙞𝙘 🎧˼", level=3)
        + rich_note("⏩ sᴇᴇᴋɪɴɢ...")
        + "<p><b>ᴛᴏ</b> : "
        + f"<code>{fmt_time(target_sec)}</code>"
        + "</p>",
    )

    try:
        media_path = await resolve_stream(song["url"])
    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ sᴇᴇᴋ ғᴀɪʟᴇᴅ — ᴄᴏᴜʟᴅ ɴᴏᴛ ʀᴇsᴏʟᴠᴇ sᴛʀᴇᴀᴍ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    try:
        await call_py.change_stream(
            chat_id,
            MediaStream(
                media_path,
                audio_parameters=AudioQuality.HIGH,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=f"-ss {target_sec}",
            ),
        )
    except Exception:
        try:
            await call_py.play(
                chat_id,
                MediaStream(
                    media_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                    ffmpeg_parameters=f"-ss {target_sec}",
                ),
            )
        except Exception as e2:
            await rich_edit(
                pm,
                rich_heading("❍ sᴇᴇᴋ ғᴀɪʟᴇᴅ", level=3)
                + rich_note(f"<code>{rich_esc(e2)}</code>"),
            )
            return

    set_seek_state(chat_id, target_sec)

    # Seek confirmation card. Keep the same compact rich-message layout:
    # branded heading, quoted status, duration and requester, followed by one
    # full-width close button.
    content = (
        rich_heading("˹𝙔𝙤𝙧 ✘ 𝙈𝙪𝙨𝙞𝙘 🎧˼", level=3)
        + rich_note("» sᴛʀᴇᴀᴍ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴇᴋᴇᴅ.")
        + "<p>"
        + f"<b>DURATION</b> : {rich_esc(fmt_time(target_sec))} MINUTES<br>"
        + f"<b>BY</b> : {rich_esc(song['requester'])}"
        + "</p>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✦ CLOSE ✦", callback_data="close_player")],
    ])
    try:
        await pm.delete()
    except Exception:
        pass
    await rich_send(bot, chat_id, content, reply_markup=kb)


# ── /seek ──────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seek_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏ sᴏɴɢ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ", level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍʙᴇʀ ᴏғ sᴇᴄᴏɴᴅs ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ 0", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/seek 30</code>")]),
        )
        return

    current_pos = get_current_position(chat_id)
    target      = current_pos + sec
    total_sec   = parse_dur(song.get("duration", "0:00"))

    if current_pos >= total_sec - 1:
        await rich_send(bot, chat_id, rich_heading("❍ sᴏɴɢ ɪs ᴀʟᴍᴏsᴛ ғɪɴɪsʜᴇᴅ, ᴄᴀɴɴᴏᴛ sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ", level=3))
        return

    if target >= total_sec:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴄᴀɴɴᴏᴛ sᴇᴇᴋ ᴛʜᴀᴛ ғᴀʀ ғᴏʀᴡᴀʀᴅ", level=3)
            + rich_kv_table([
                ("ᴄᴜʀʀᴇɴᴛ ᴘᴏsɪᴛɪᴏɴ", f"<code>{fmt_time(current_pos)}</code>"),
                ("sᴏɴɢ ᴅᴜʀᴀᴛɪᴏɴ", f"<code>{fmt_time(total_sec)}</code>"),
            ]),
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seekback ──────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seekback(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seekback_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏ sᴏɴɢ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ", level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍʙᴇʀ ᴏғ sᴇᴄᴏɴᴅs ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ 0", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/seekback 30</code>")]),
        )
        return

    target = max(0, get_current_position(chat_id) - sec)

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seek (no args) ────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?$")
    & group_allowed
    & user_allowed
)
async def seek_usage(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    # Keep the no-argument help response simple. Do not render the
    # command instructions as a table.
    content = (
        rich_heading("˹𝙔𝙤𝙧 ✘ 𝙈𝙪𝙨𝙞𝙘 🎧˼", level=3)
        + rich_note("❍ sᴇᴇᴋ ᴜsᴀɢᴇ")
        + "<p>"
        + "<b>ғᴏʀᴡᴀʀᴅ:</b> <code>/seek 30</code><br>"
        + "<b>ʙᴀᴄᴋᴡᴀʀᴅ:</b> <code>/seekback 30</code>"
        + "</p>"
    )

    await rich_send(bot, chat_id, content)

