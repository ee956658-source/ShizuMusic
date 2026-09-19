# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import logging
import time

from pyrogram import Client
from pyrogram.enums import ParseMode

import config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

LOGGER         = logging.getLogger(__name__)
bot_start_time = time.time()

# ── Bot client ────────────────────────────────────────────────────────────────
bot = Client(
    config.SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    parse_mode=ParseMode.DEFAULT,
    in_memory=True,
)

# ── Assistant (userbot) for voice chats ───────────────────────────────────────
assistant = Client(
    "assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.STRING_SESSION,
    in_memory=True,
)

# ── PyTgCalls ─────────────────────────────────────────────────────────────────
# IMPORTANT: PyTgCalls creates asyncio primitives (including its ChatLock) in
# its constructor.  It must therefore be instantiated inside the same running
# event loop used by the bot/assistant, not while this module is imported.
call_py = None
