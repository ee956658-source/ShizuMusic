# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import importlib
import inspect
import os
import re
import sys
import threading
import time

import requests
from flask import Flask
from pyrogram import idle
from pyrogram.types import BotCommand

import config
from ShizuMusic import LOGGER, assistant, bot, call_py
from ShizuMusic.modules import ALL_MODULES
from ShizuMusic.utils.rich_ui import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_send,
)

ASSISTANT_USERNAME: str = ""

# ── Flask health check ────────────────────────────────────────────────────────

_flask = Flask(__name__)


@_flask.route("/")
def _home():
    return "❍ ꜱʜɪᴢᴜᴍᴜꜱɪᴄ ɪꜱ ʀᴜɴɴɪɴɢ ᴍᴀᴅᴇ ʙʏ ʙᴀᴅᴍᴜɴᴅᴀ 💕", 200


@_flask.route("/health")
def _health():
    return "OK", 200


def _run_flask() -> None:
    _flask.run(host="0.0.0.0", port=config.PORT, use_reloader=False)


# ── Keep-Alive ────────────────────────────────────────────────────────────────

def _keep_alive() -> None:
    url = os.getenv("RENDER_EXTERNAL_URL", f"http://0.0.0.0:{config.PORT}")
    while True:
        try:
            requests.get(url, timeout=10)
            LOGGER.info(f"Keep-alive ping sent → {url}")
        except Exception as e:
            LOGGER.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)


# ── Startup notification ──────────────────────────────────────────────────────


async def _notify_owner(me, assistant_username: str) -> None:
    if not config.LOGGER_ID:
        return

    try:
        content = (
            rich_heading(
                "🎵 ꜱʜɪᴢᴜᴍᴜꜱɪᴄ ꜱᴛᴀʀᴛᴇᴅ 💕",
                level=3
            )
            + rich_kv_table([
                (
                    "ʙᴏᴛ",
                    f"@{rich_esc(me.username or 'N/A')}"
                ),
                (
                    "ᴀꜱꜱɪꜱᴛᴀɴᴛ",
                    f"@{rich_esc(assistant_username)}"
                ),
            ])
        )

        await rich_send(
            bot,
            config.LOGGER_ID,
            content,
        )

    except Exception as e:
        LOGGER.warning(
            f"Logger Notification Error : {e}"
        )

# ── Main ──────────────────────────────────────────────────────────────────────

async def _main() -> None:
    # 1. MongoDB
    try:
        from ShizuMusic.utils.db import start_mongo
        ok = start_mongo()
        if ok:
            LOGGER.info("MongoDB ready.")
        else:
            LOGGER.warning("MongoDB not connected — continuing without DB.")
    except Exception as e:
        LOGGER.warning(f"MongoDB startup error: {e} — continuing without DB.")

    # 2. Flask
    threading.Thread(target=_run_flask, daemon=True).start()
    LOGGER.info(f"Flask health server on port {config.PORT}")

    # 3. Keep-alive ping
    threading.Thread(target=_keep_alive, daemon=True).start()
    LOGGER.info("Keep-alive thread started")

    # 4. Start Bot + Assistant on ONE running event loop.
    # Kurigram binds a Client to the loop on which start() is awaited. Starting
    # them with the synchronous wrapper leaves the assistant bound to a stopped
    # loop, which breaks assistant calls from bot handlers (JOIN ERROR / loop mismatch).
    try:
        for attempt in range(10):
            try:
                await bot.start()
                LOGGER.info("Bot client started")
                break
            except Exception as e:
                if "FLOOD_WAIT" in str(e):
                    m = re.search(r"(\d+)", str(e))
                    wait = min(int(m.group(1)) + 5 if m else 300, 1800)
                    LOGGER.warning(
                        f"FLOOD_WAIT — sleeping {wait}s (attempt {attempt + 1}/10)"
                    )
                    await asyncio.sleep(wait)
                else:
                    LOGGER.error(f"Bot start failed: {e}")
                    raise
        else:
            raise RuntimeError("Bot failed to start after 10 attempts")

        await assistant.start()
        LOGGER.info("Assistant client started")

        # PyTgCalls was created before the async loop existed, so point its loop
        # at the same live loop before starting it.
        call_py.loop = asyncio.get_running_loop()
        result = call_py.start()
        if inspect.isawaitable(result):
            await result
        LOGGER.info("PyTgCalls started")

        LOGGER.info(
            "Event loops: bot=%s assistant=%s pytgcalls=%s",
            id(getattr(bot, "_loop", None)),
            id(getattr(assistant, "_loop", None)),
            id(getattr(call_py, "loop", None)),
        )
    except Exception as e:
        LOGGER.error(f"Client startup failed: {e}", exc_info=True)
        try:
            if assistant.is_connected:
                await assistant.stop()
        except Exception:
            pass
        try:
            if bot.is_connected:
                await bot.stop()
        except Exception:
            pass
        sys.exit(1)

    me = await bot.get_me()
    LOGGER.info(f"Bot: @{me.username}")

    # 5. Set bot commands
    try:
        await bot.set_bot_commands([
            BotCommand("start",  "✧ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ✧"),
            BotCommand("help",   "✧ ɢᴇᴛ ʜᴇʟᴘ ᴍᴇɴᴜ ✧"),
            BotCommand("ai",     "✧ ᴀsᴋ ᴀɪ ✧"),
            BotCommand("play",   "✧ ᴘʟᴀʏ ᴀ sᴏɴɢ ✧"),
            BotCommand("pause",  "✧ ᴘᴀᴜsᴇ ᴘʟᴀʏʙᴀᴄᴋ ✧"),
            BotCommand("resume", "✧ ʀᴇsᴜᴍᴇ ᴘʟᴀʏʙᴀᴄᴋ ✧"),
            BotCommand("skip",   "✧ sᴋɪᴘ sᴏɴɢ ✧"),
            BotCommand("stop",   "✧ sᴛᴏᴘ & ᴄʟᴇᴀʀ ✧"),
            BotCommand("ping",   "✧ ʙᴏᴛ sᴛᴀᴛs ✧"),
            BotCommand("loop",   "✧ ʀᴇᴘᴇᴀᴛ ᴄᴜʀʀᴇɴᴛ sᴏɴɢ ✧"),
        ])
        LOGGER.info("Bot commands set")
    except Exception as e:
        LOGGER.warning(f"Could not set bot commands: {e}")

    # 6. Assistant identity
    try:
        am = await assistant.get_me()
        ASSISTANT_USERNAME = am.username or ""
        LOGGER.info(f"Assistant: @{ASSISTANT_USERNAME}")
    except Exception as e:
        LOGGER.error(f"Assistant identity check failed: {e}")

    # 7. Block middleware — MUST run before plugins load
    try:
        from ShizuMusic.utils.decorators import register_block_middleware
        register_block_middleware()
        LOGGER.info("Block middleware registered")
    except Exception as e:
        LOGGER.warning(f"Block middleware load failed: {e}")

    # 8. Load modules
    for mod in ALL_MODULES:
        try:
            importlib.import_module(f"ShizuMusic.modules.{mod}")
            LOGGER.info(f"Loaded module: {mod}")
        except Exception as e:
            LOGGER.error(f"Failed to load module {mod}: {e}", exc_info=True)

    # 9. Stream-end handler
    try:
        import ShizuMusic.core.call  # noqa: F401
    except Exception as e:
        LOGGER.error(f"Failed to load call handler: {e}", exc_info=True)

    # 10. Notify owner
    await _notify_owner(me, ASSISTANT_USERNAME)

    # 11. Watchdog
    from ShizuMusic.core.watcher import watchdog
    asyncio.create_task(watchdog())
    LOGGER.info("Watchdog started")

    LOGGER.info("ShizuMusic is running")

    try:
        await idle()
    finally:
        try:
            await bot.stop()
        except Exception:
            pass

        try:
            await assistant.stop()
        except Exception:
            pass

        LOGGER.info("✧ ShizuMusic stopped ✧")


if __name__ == "__main__":
    asyncio.run(_main())
