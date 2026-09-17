# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

"""
Assistant utility functions.
Handles checking whether the assistant is in a group and auto-joining it.
Previously this logic was inline in play.py — now centralised here.
"""

import asyncio

from pyrogram.errors import RPCError, UserAlreadyParticipant
from pyrogram.types import Message

import time

from ShizuMusic import assistant, bot
from ShizuMusic.utils.rich_ui import rich_edit, rich_esc, rich_heading, rich_note

# Cache assistant membership for 10 minutes (saves 0.3-0.8s per /play)
_assistant_cache: dict[int, tuple] = {}  # chat_id -> (status, expire_ts)
_me_id: int | None = None
_CACHE_TTL = 600


async def is_assistant_in(chat_id: int):
    """
    Check whether the assistant is a member of the given group.
    Cached 10 min to avoid Telegram API lag on every /play.

    Returns:
        True     — assistant is present
        False    — assistant is not present
        "banned" — assistant was banned from the group
    """
    now = time.time()
    cached = _assistant_cache.get(chat_id)
    if cached and cached[1] > now:
        return cached[0]

    try:
        global _me_id
        if _me_id is None:
            me = await assistant.get_me()
            _me_id = me.id
        member = await assistant.get_chat_member(chat_id, _me_id)
        status = member.status is not None
        _assistant_cache[chat_id] = (status, now + _CACHE_TTL)
        return status

    except Exception as e:
        err = str(e)
        if "USER_BANNED" in err or "Banned" in err:
            _assistant_cache[chat_id] = ("banned", now + 60)
            return "banned"
        _assistant_cache[chat_id] = (False, now + 30)
        return False


async def try_join_assistant(chat_id: int, pm: Message) -> bool:
    """
    Attempt to make the assistant join the group via invite link.

    Args:
        chat_id: Target group chat ID.
        pm:      Status message to edit with progress / error text.

    Returns:
        True on success, False on failure.
    """
    try:
        invite_link = await bot.export_chat_invite_link(chat_id)

    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ ɪ ɴᴇᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴘᴇʀᴍɪssɪᴏɴ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    try:
        # Normalise joinchat link format
        if invite_link.startswith("https://t.me/+"):
            invite_link = invite_link.replace(
                "https://t.me/+",
                "https://t.me/joinchat/",
            )

        await assistant.join_chat(invite_link)
        await asyncio.sleep(0.8)
        return True

    except UserAlreadyParticipant:
        return True

    except RPCError as e:
        await rich_edit(
            pm,
            rich_heading("❍ ᴀssɪsᴛᴀɴᴛ ᴊᴏɪɴ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ ᴊᴏɪɴ ᴇʀʀᴏʀ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False
        
