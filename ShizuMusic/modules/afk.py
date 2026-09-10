import time

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed


# user_id: {"time": timestamp, "reason": reason, "name": name}
AFK_USERS = {}


def fancy_name(name: str) -> str:
    result = []

    for char in name:
        if "A" <= char <= "Z":
            result.append(chr(ord(char) - ord("A") + 0x1D400))
        elif "a" <= char <= "z":
            result.append(chr(ord(char) - ord("a") + 0x1D41A))
        else:
            result.append(char)

    return "".join(result)


def mention_user(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{fancy_name(name)}</a>'


def format_afk_time(seconds: int) -> str:
    seconds = max(0, int(seconds))

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []

    if hours:
        parts.append(f"{hours}ʜ")

    if minutes:
        parts.append(f"{minutes}ᴍ")

    if secs or not parts:
        parts.append(f"{secs}s")

    return ":".join(parts)


# ── /afk command ──────────────────────────────────────────────────────────────

@bot.on_message(filters.command("afk") & user_allowed)
async def afk_handler(_, message: Message) -> None:

    user = message.from_user

    if not user:
        return

    parts = message.text.split(maxsplit=1) if message.text else []
    reason = parts[1].strip() if len(parts) > 1 else ""

    AFK_USERS[user.id] = {
        "time": time.time(),
        "reason": reason,
        "name": user.first_name or "User",
    }

    name = mention_user(
        user.id,
        user.first_name or "User"
    )

    await message.reply_text(
        f"{name} is now afk"
    )


# ── AFK detection + return ───────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & ~filters.command("afk")
    & user_allowed,
    group=10
)
async def afk_handler_messages(_, message: Message) -> None:

    user = message.from_user

    if not user:
        return

    # ── User came back online ────────────────────────────────────────────────
    if user.id in AFK_USERS:

        data = AFK_USERS.pop(user.id)

        elapsed = format_afk_time(
            time.time() - data["time"]
        )

        name = mention_user(
            user.id,
            user.first_name or data["name"]
        )

        text = f"{name} is back online since {elapsed}"

        if data["reason"]:
            text += f"\nReason: {data['reason']}"

        await message.reply_text(text)

        return

    # ── Check replied-to user ────────────────────────────────────────────────
    if (
        message.reply_to_message
        and message.reply_to_message.from_user
    ):

        target = message.reply_to_message.from_user

        if target.id in AFK_USERS:

            data = AFK_USERS[target.id]

            elapsed = format_afk_time(
                time.time() - data["time"]
            )

            name = mention_user(
                target.id,
                target.first_name or data["name"]
            )

            await message.reply_text(
                f"{name} is afk since {elapsed}"
            )

            return

    # ── Check mentioned users ────────────────────────────────────────────────
    try:
        mentioned_users = await message.get_users()
    except Exception:
        mentioned_users = []

    for target in mentioned_users:

        if target.id in AFK_USERS:

            data = AFK_USERS[target.id]

            elapsed = format_afk_time(
                time.time() - data["time"]
            )

            name = mention_user(
                target.id,
                target.first_name or data["name"]
            )

            await message.reply_text(
                f"{name} is afk since {elapsed}"
            )

            break
