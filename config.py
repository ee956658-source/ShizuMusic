"""
config.py — All environment variables in one place.
Copy sample.env → .env and fill in your values.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ──────────────────────────────────────────────────────────────────
API_ID          = int(os.environ["API_ID"])
API_HASH        = os.environ["API_HASH"]
BOT_TOKEN       = os.environ["BOT_TOKEN"]
STRING_SESSION  = os.environ["STRING_SESSION"]
MONGO_DB_URL    = os.environ["MONGO_DB_URL"]
OWNER_ID        = int(os.environ["OWNER_ID"])

# ── Optional ──────────────────────────────────────────────────────────────────
BOT_NAME         = os.getenv("BOT_NAME", "YORXMUSIC")
BOT_LINK         = os.getenv("BOT_LINK", "https://t.me/YorMusicXbot")
UPDATES_CHANNEL  = os.getenv("UPDATES_CHANNEL", "https://t.me/VIP_PFP_SP")
SUPPORT_GROUP    = os.getenv("SUPPORT_GROUP", "https://t.me/zpaveldurov")
LOGGER_ID        = int(os.getenv("LOGGER_ID", "0"))
PING_IMG_URL     = os.getenv("PING_IMG_URL", "https://files.catbox.moe/ddzvc0.jpg",)
SESSION_NAME     = os.getenv("SESSION_NAME", "yorxmusic")
PORT             = int(os.getenv("PORT", 10000))

# ── NSFW Moderation API ─────────────────────────────────────────────────────
#NSFW_API_URL = os.getenv("NSFW_API_URL", "https://ai-moderation-api-khyr.onrender.com")
#NSFW_API_KEY = os.getenv("NSFW_API_KEY", "nsfwBad")

# Custom detection thresholds — sent with every /detect/upload call.
#NSFW_THRESHOLDS = {
#    "porn": float(os.getenv("NSFW_THRESHOLD_PORN", "0.7")),
#    "sexy": float(os.getenv("NSFW_THRESHOLD_SEXY", "0.8")),
#}

#── Start ───────────────────────────────────────────────────────────────────────
START_PHOTOS = [
    "https://files.catbox.moe/sfqdhn.jpg",
]

# ── NexGenBots API (fast stream) ──────────────────────────────────────────────
NEXGEN_API_KEY       = os.getenv("NEXGEN_API_KEY", "30DxNexGenBots66383d")
NEXGEN_API_URL       = os.getenv("NEXGEN_API_URL", "https://pvtz.nexgenbots.xyz")
NEXGEN_VIDEO_API_URL = os.getenv("NEXGEN_VIDEO_API_URL", "https://api.video.nexgenbots.xyz")

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_DURATION_SECONDS = 1800   # 30 minutes
QUEUE_LIMIT          = 20
COOLDOWN             = 2      # seconds between /play per chat (fast bots use 2-3s)


#BLOCKED_EXTENSIONS = [
#    ".zip",
#    ".rar",
#    ".7z",
#    ".apk",
#    ".exe",
#    ".py",
#    ".js",
#    ".go",
#    ".php",
#]


# ── AI Providers (optional) ────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "45"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1200"))
AI_SYSTEM_PROMPT = os.getenv("AI_SYSTEM_PROMPT", "You are the helpful AI assistant inside a Telegram music bot. Answer clearly, accurately, and concisely. Do not claim to have abilities you do not have.")
