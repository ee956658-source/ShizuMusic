# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import random
import time

from pyrogram.enums import ParseMode
from pyrogram.raw.functions.phone import CreateGroupCall
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    AudioQuality,
    MediaStream,
    VideoQuality,
    ChatUpdate,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
)

import config

from ShizuMusic import (
    LOGGER,
    assistant,
    bot,
    call_py,
)

from ShizuMusic.core.queue import (
    remove_from_queue,
)

from ShizuMusic.utils.formatters import (
    parse_dur,
    progress_bar,
    short,
)

from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.player_thumbnail import make_player_thumbnail

from ShizuMusic.utils.youtube import (
    resolve_stream,
)


def _support_updates_pills() -> str:
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        "🍬 sᴜᴘᴘᴏʀᴛ</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 ᴜᴘᴅᴀᴛᴇs</tg-button>"
        "</p>"
    )


# ─────────────────────────────────────────────
# NOW PLAYING CONTENT
# ─────────────────────────────────────────────


def _now_playing_content(song: dict) -> str:
    """Now-playing message content."""

    thumb = song.get("thumbnail")

    return (
        (rich_img(thumb) if thumb else "")
        + "<p>"
        + "<small>streaming 🎶</small><br><br>"
        + f"<small>Title: {rich_esc(short(song['title']))}</small><br>"
        + f"<small>Duration: {rich_esc(song.get('duration', '?'))}</small><br>"
        + f"<small>Requested by: {rich_esc(song['requester'])}</small>"
        + "</p>"
    )


def _now_playing_kb(elapsed: float, total: float) -> InlineKeyboardMarkup:
    bar = progress_bar(elapsed, total)

    btns = [
        InlineKeyboardButton("▷", callback_data="resume"),
        InlineKeyboardButton("II", callback_data="pause"),
        InlineKeyboardButton("⥁", callback_data="replay"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢", callback_data="stop"),
    ]

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(bar, callback_data="noop")],
        btns,
    ])


# ─────────────────────────────────────────────
# PROGRESS UPDATER
# ─────────────────────────────────────────────

async def _update_progress(
    chat_id: int,
    msg: Message,
    start_t: float,
    total: float,
    content: str,
) -> None:

    while True:

        elapsed = min(time.time() - start_t, total)
        kb = _now_playing_kb(elapsed, total)
        # Keep the Close button when the progress updater refreshes the
        # keyboard. Otherwise the updater would replace the initial keyboard
        # after ~18 seconds and the Close button would disappear.
        kb = InlineKeyboardMarkup(
            list(kb.inline_keyboard)
            + [[InlineKeyboardButton("Close", callback_data="close_player")]]
        )

        try:
            # Player messages are sent as photos so the generated/edit thumbnail
            # remains visible while the controls/progress are updated.
            if getattr(msg, "photo", None):
                caption = rich_to_caption(content)
                await bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=msg.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb,
                )
            else:
                await rich_edit(msg, content, reply_markup=kb)

        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                break

        if elapsed >= total:
            break

        await asyncio.sleep(18)


def rich_to_caption(content: str) -> str:
    """Flatten the rich player content into Telegram photo-caption HTML."""
    import re
    text = re.sub(r"</?(?:h[1-6]|table|thead|tbody|tr|th|td|p|img)\b[^>]*>", "", content, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    return text.strip()


# ─────────────────────────────────────────────
# AUTO START VC
# ─────────────────────────────────────────────

async def _ensure_vc(chat_id: int) -> bool:

    try:

        chat_id = int(chat_id)
        chat = await assistant.get_chat(chat_id)

        await assistant.invoke(
            CreateGroupCall(
                peer=await assistant.resolve_peer(chat.id),
                random_id=random.randint(10000, 99999),
            )
        )

        LOGGER.info(f"[VC] Created in {chat_id}")
        await asyncio.sleep(0.25)  # reduced for speed
        return True

    except TelegramServerError as e:
        LOGGER.error(f"[VC] TelegramServerError: {e}")
        await rich_send(
            bot,
            chat_id,
            rich_heading(
                "❍ ᴠᴄ sᴛᴀʀᴛ ғᴀɪʟᴇᴅ (Telegram Server)",
                level=3,
            )
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    except Exception as e:

        err = str(e).lower()

        # already active
        if "already" in err or "groupcall_already_started" in err:
            return True

        # admin rights missing
        if "chat_admin_required" in err or "admin" in err:
            await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "❍ ᴠᴄ sᴛᴀʀᴛ ᴘᴇʀᴍɪssɪᴏɴ ᴍɪssɪɴɢ",
                    level=3,
                )
                + rich_note(
                    "ɢɪᴠᴇ ᴀssɪsᴛᴀɴᴛ » ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs, ᴀᴅᴍɪɴ ʀɪɢʜᴛs"
                ),
            )
            return False

        LOGGER.error(f"[VC ERROR] {e}")

        await rich_send(
            bot,
            chat_id,
            rich_heading(
                "❍ ᴠᴄ sᴛᴀʀᴛ ғᴀɪʟᴇᴅ",
                level=3,
            )
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )

        return False


# ─────────────────────────────────────────────
# MAIN PLAY FUNCTION
# ─────────────────────────────────────────────

async def play_song(
    chat_id: int,
    message: Message,
    song: dict,
) -> None:

    chat_id = int(chat_id)
    url = song.get("url")

    if not url:
        return

    # SPEED: skip "loading..." Telegram edit — every API call costs 200-500ms.
    # Stream first, UI later.

    is_video = song.get("video", False)

    try:
        media_path = await resolve_stream(url, video=is_video)

    except Exception as e:

        try:
            remove_from_queue(
                chat_id,
                0,
            )
        except Exception:
            pass

        await rich_send(
            bot,
            chat_id,
            rich_heading(
                "❍ ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ",
                level=3,
            )
            + rich_note(
                f"<code>{rich_esc(e)}</code>"
            ),
        )

        return

    # Effects only on local files (remote NexGen streams skip — saves time)
    if not is_video and not str(media_path).startswith("http"):

        try:
            from ShizuMusic.modules.effects import maybe_apply_effects

            media_path = await maybe_apply_effects(
                chat_id,
                media_path,
            )

        except Exception as fx_err:
            LOGGER.warning(
                f"[Effects] Skipped: {fx_err}"
            )

    # ─────────────────────────────────────────
    # PLAY STREAM (simple direct — no NexGen lag)
    # ─────────────────────────────────────────

    played = False

    # A cached remote URL can expire even though resolve_stream reports a
    # cache hit. Give the call engine a bounded timeout and refresh the stream
    # once before declaring playback failed. This prevents the assistant from
    # sitting in VC silently when a stale stream URL is returned.
    playback_error = None

    for attempt in range(2):

        try:

            if is_video:

                await asyncio.wait_for(
                    call_py.play(
                        chat_id,
                        MediaStream(
                            media_path,
                            audio_parameters=AudioQuality.HIGH,
                            video_parameters=VideoQuality.HD_720p,
                        ),
                    ),
                    timeout=12,
                )

            else:
                # HIGH is fine; stream URL starts immediately (no local download)
                await asyncio.wait_for(
                    call_py.play(
                        chat_id,
                        MediaStream(
                            media_path,
                            audio_parameters=AudioQuality.HIGH,
                            video_flags=MediaStream.Flags.IGNORE,
                        ),
                    ),
                    timeout=12,
                )

            played = True
            break

        except NoActiveGroupCall:

            if attempt == 0:

                LOGGER.info(
                    f"[VC] NoActiveGroupCall — Creating VC in {chat_id}"
                )

                ok = await _ensure_vc(
                    chat_id
                )

                if ok:
                    continue

                try:
                    remove_from_queue(
                        chat_id,
                        0,
                    )
                except Exception:
                    pass

                return

        except TelegramServerError as e:

            LOGGER.error(
                f"[PLAY] TelegramServerError: {e}"
            )

            try:
                remove_from_queue(
                    chat_id,
                    0,
                )
            except Exception:
                pass

            await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ (Telegram Server)",
                    level=3,
                )
                + rich_note(
                    f"<code>{rich_esc(e)}</code>"
                ),
            )

            return

        except Exception as e:

            playback_error = e
            err = str(e).lower()

            # If a remote cached URL is stale/expired, resolve a fresh URL once.
            # Do not add a download wait to the normal successful path.
            if attempt == 0 and isinstance(media_path, str) and media_path.startswith("http"):
                LOGGER.warning(f"[PLAY] Stream rejected/timeout; refreshing URL: {e}")
                try:
                    media_path = await resolve_stream(url, video=is_video)
                    continue
                except Exception as refresh_err:
                    LOGGER.warning(f"[PLAY] Stream refresh failed: {refresh_err}")

            vc_missing = any(
                x in err
                for x in (
                    "groupcallnotfound",
                    "not_in_group_call",
                    "groupcall_forbidden",
                    "not in group call",
                    "no active group call",
                )
            )

            if vc_missing and attempt == 0:

                LOGGER.info(
                    f"[VC] Creating VC in {chat_id}"
                )

                ok = await _ensure_vc(
                    chat_id
                )

                if ok:
                    continue

                try:
                    remove_from_queue(
                        chat_id,
                        0,
                    )
                except Exception:
                    pass

                return

            if (
                "chat_admin_required" in err
                or "admin" in err
            ):

                try:
                    remove_from_queue(
                        chat_id,
                        0,
                    )
                except Exception:
                    pass

                await rich_send(
                    bot,
                    chat_id,
                    rich_heading(
                        "❍ ᴠᴄ sᴛᴀʀᴛ ᴘᴇʀᴍɪssɪᴏɴ ᴍɪssɪɴɢ",
                        level=3,
                    )
                    + rich_note(
                        "ᴘʟᴇᴀsᴇ ɢɪᴠᴇ » ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs, "
                        "ᴀᴅᴍɪɴ ʀɪɢʜᴛs · ᴀssɪsᴛᴀɴᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ"
                    ),
                )

                LOGGER.error(
                    f"[ADMIN ERROR] {e}"
                )

                return

            try:
                remove_from_queue(
                    chat_id,
                    0,
                )
            except Exception:
                pass

            await rich_send(
                bot,
                chat_id,
                rich_heading(
                    "❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ",
                    level=3,
                )
                + rich_note(
                    f"<code>{rich_esc(e)}</code>"
                ),
            )

            LOGGER.error(
                f"[PLAY ERROR] {e}"
            )

            return

    if not played:
        return

    # ─────────────────────────────────────────
    # RESET SEEK
    # ─────────────────────────────────────────

    try:

        from ShizuMusic.modules.seek import set_seek_state

        set_seek_state(
            chat_id,
            0,
        )

    except Exception:
        pass

    # ─────────────────────────────────────────
    # DATABASE TRACKING
    # ─────────────────────────────────────────

    try:

        from ShizuMusic.database import (
            add_served_chat,
            add_served_user,
            increment_play_count,
        )

        add_served_chat(
            chat_id
        )

        requester_id = song.get(
            "requester_id"
        )

        if requester_id:
            add_served_user(
                requester_id
            )

        increment_play_count(
            chat_id
        )

    except Exception as db_err:

        LOGGER.warning(
            f"[DB ERROR] {db_err}"
        )

    # ─────────────────────────────────────────
    # NOW PLAYING UI
    # ─────────────────────────────────────────

    total = parse_dur(
        song.get(
            "duration",
            "0:00",
        )
    )

    # Generate a separate edited/player thumbnail from the YouTube artwork.
    # If rendering fails, fall back to the existing rich-image player.
    player_thumb = await make_player_thumbnail(
        song.get("thumbnail", ""),
        song.get("title", "Unknown Song"),
        song.get("duration", "0:00"),
    )

    content = _now_playing_content(song)

    kb = _now_playing_kb(0, total)
    # Telegram photo caption buttons: add a dedicated Close action below the
    # player, matching the requested expanded-player layout.
    kb = InlineKeyboardMarkup(
        list(kb.inline_keyboard)
        + [[InlineKeyboardButton("Close", callback_data="close_player")]]
    )

    pmsg = None
    if player_thumb:
        try:
            pmsg = await bot.send_photo(
                chat_id=chat_id,
                photo=player_thumb,
                caption=rich_to_caption(content),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            if message is not None:
                try:
                    await message.delete()
                except Exception:
                    pass
        except Exception as e:
            LOGGER.warning(f"[PLAYER THUMB] send_photo failed: {e}")

    if pmsg is None:
        try:
            if message is not None:
                pmsg = await rich_edit(message, content, reply_markup=kb)
            if pmsg is None:
                pmsg = await rich_send(bot, chat_id, content, reply_markup=kb)
        except Exception:
            pmsg = await rich_send(bot, chat_id, content, reply_markup=kb)

    asyncio.create_task(
        _update_progress(
            chat_id,
            pmsg,
            time.time(),
            total,
            content,
        )
    )

    # ─────────────────────────────────────────
    # LOGGER
    # ─────────────────────────────────────────

    if config.LOGGER_ID:

        logger_content = (
            rich_heading(
                "🎧 #ɴᴏᴡᴘʟᴀʏɪɴɢ",
                level=3,
            )
            + rich_kv_table(
                [
                    (
                        "ᴛɪᴛʟᴇ",
                        rich_esc(
                            song.get(
                                "title",
                                "?",
                            )
                        ),
                    ),
                    (
                        "ᴅᴜʀᴀᴛɪᴏɴ",
                        rich_esc(
                            song.get(
                                "duration",
                                "?",
                            )
                        ),
                    ),
                    (
                        "ʙʏ",
                        rich_esc(
                            song.get(
                                "requester",
                                "?",
                            )
                        ),
                    ),
                ]
            )
        )

        asyncio.create_task(
            rich_send(
                bot,
                config.LOGGER_ID,
                logger_content,
            )
        )
