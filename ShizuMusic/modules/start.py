# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import enums, filters
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from config import START_PHOTOS
from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    sanitize_display_name,
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


# ── /start ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & user_allowed)
async def start_handler(_, message: Message) -> None:

    uid = message.from_user.id
    name = sanitize_display_name(message.from_user.first_name)
    chat_id = message.chat.id
    chat_type = message.chat.type
    photo = random.choice(config.START_PHOTOS)

    # ── Delete the user's /start command message ──────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    try:
        add_served_user(uid)
        add_served_chat(chat_id)
    except Exception:
        pass

    # ── Private ───────────────────────────────────────────────────────────────
    if chat_type == ChatType.PRIVATE:

        caption = (
            rich_img(photo)
            + rich_note(
                f"<p>ʜᴇʏ <a href='tg://user?id={uid}'>{rich_esc(name)}</a> — "
                "ɢʟᴀᴅ ʏᴏᴜ ғᴏᴜɴᴅ ᴍᴇ! 🎧♬</p>"
                "<p>ᴛʜɪs ɪs ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴍᴜsɪᴄ ᴄᴏʀɴᴇʀ ✦🎶</p>"
                "<p>ᴄʜᴏᴏsᴇ ᴛʜᴇ sᴏɴɢ • ɪ ʜᴀɴᴅʟᴇ ᴛʜᴇ ᴠɪʙᴇ⚡</p>"
                "<p>sᴍᴀʀᴛ ᴄᴏɴᴛʀᴏʟs • sᴍᴏᴏᴛʜ ᴘʟᴀʏʙᴀᴄᴋ🎧</p>"
                "<p>ᴄʟᴇᴀɴ, ʟᴏᴡ-ʟᴀɢ sᴛʀᴇᴀᴍɪɴɢ.</p>"
                "<p>────────────────────</p>"
                "<p>ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ɢʀᴏᴜᴘ<br>"
                "ɴᴏ ᴀᴅs<br>"
                "ᴏᴡɴᴇʀ : @iucrazy_ll</p>"
                "<p>────────────────────</p>"
                "<p>ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ "
                "ᴀʙᴏᴜᴛ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs.</p>"
            )
        )

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    " ᴧᴅᴅ ᴍᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ",
                    url=f"{config.BOT_LINK}?startgroup=true",
                    style=enums.ButtonStyle.DEFAULT,
                )
            ],
            [
                InlineKeyboardButton(
                    " ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs ",
                    callback_data="show_help",
                    style=enums.ButtonStyle.DEFAULT,
                )
            ],
            [
                InlineKeyboardButton(
                    " ᴏᴡɴᴇʀ ",
                    url=f"tg://user?id={config.OWNER_ID}",
                    style=enums.ButtonStyle.DEFAULT,
                ),
                InlineKeyboardButton(
                    " ᴜᴘᴅᴀᴛᴇs ",
                    url=config.UPDATES_CHANNEL,
                    style=enums.ButtonStyle.DEFAULT,
                ),
            ],
        ])

        try:
            sent = await rich_send(
                bot,
                chat_id,
                caption,
                reply_markup=kb,
            )
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(
                bot,
                chat_id,
                caption,
                reply_markup=kb,
            )

        try:
            add_broadcast_chat(chat_id, "private")
        except Exception:
            pass

        # ── Log new user to LOGGER_ID ────────────────────────────────────────
        if config.LOGGER_ID:
            try:
                username = message.from_user.username
                username_display = (
                    f"@{rich_esc(username)}" if username else "N/A"
                )

                logger_caption = (
                    rich_heading("#ɴᴇᴡᴜsᴇʀ sᴛᴀʀᴛᴇᴅ", level=2)
                    + rich_kv_table([
                        (
                            "ɴᴀᴍᴇ",
                            f'<a href="tg://user?id={uid}">'
                            f"{rich_esc(name)}</a>",
                        ),
                        ("ɪᴅ", f"<code>{uid}</code>"),
                        ("ᴜsᴇʀɴᴀᴍᴇ", username_display),
                    ])
                )

                await rich_send(
                    bot,
                    config.LOGGER_ID,
                    logger_caption,
                )

            except Exception as e:
                print(
                    f"[start_handler] Failed to send LOGGER_ID message: {e}"
                )

    # ── Group ────────────────────────────────────────────────────────────────
    else:
        chat_title = message.chat.title or "this chat"

        caption = (
            rich_img(photo)
            + f"<p>❍ ʜᴇʏ "
            f"<a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
            f"ᴛʜɪs ɪs <b>{rich_esc(config.BOT_NAME)}</b></p>"
            + rich_note(
                f"ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ "
                f"{rich_esc(chat_title)}. "
                f"{rich_esc(name)} ᴄᴀɴ ɴᴏᴡ ᴘʟᴀʏ sᴏɴɢs ʜᴇʀᴇ."
            )
            + _support_updates_pills()
        )

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    " ᴧᴅᴅ ᴍᴇ ʙᴀʙʏ ",
                    url=f"{config.BOT_LINK}?startgroup=true",
                    style=enums.ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    "🍬 sᴜᴘᴘᴏʀᴛ 🍬",
                    url=config.SUPPORT_GROUP,
                    style=enums.ButtonStyle.SUCCESS,
                ),
            ],
            [
                InlineKeyboardButton(
                    " ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs ",
                    callback_data="show_help",
                    style=enums.ButtonStyle.PRIMARY,
                )
            ],
        ])

        try:
            sent = await rich_send(
                bot,
                chat_id,
                caption,
                reply_markup=kb,
            )
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(
                bot,
                chat_id,
                caption,
                reply_markup=kb,
            )

        admin_msg = (
            rich_heading("ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ! 🥀", level=2)
            + rich_note(
                "<p>ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ "
                "ᴡɪᴛʜ ᴛʜᴇsᴇ ᴘᴇʀᴍɪssɪᴏɴs:</p>"
                "<p>❍ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs<br>"
                "❍ ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs<br>"
                "❍ ɪɴᴠɪᴛᴇ ᴜsᴇʀs</p>"
            )
            + rich_note(
                "ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ᴘᴇʀᴍs "
                "sᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs ᴡᴏɴ'ᴛ ᴡᴏʀᴋ! 🚫"
            )
        )

        admin_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⚡ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ⚡",
                url=f"tg://user?id={(await bot.get_me()).id}",
                style=enums.ButtonStyle.DANGER,
            )
        ]])

        try:
            admin_sent = await rich_send(
                bot,
                chat_id,
                admin_msg,
                reply_markup=admin_kb,
            )
        except Exception:
            pass

        try:
            add_broadcast_chat(chat_id, "group")
        except Exception:
            pass


# ── /help ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("help") & user_allowed)
async def help_handler(_, message: Message) -> None:

    uid = message.from_user.id
    name = sanitize_display_name(message.from_user.first_name)

    # ── Delete the user's /help command message ───────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "ᴧᴅᴍɪɴ",
                callback_data="help_admin",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "ᴧ-ᴘʟᴀʏ",
                callback_data="help_autoplay",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "ɢ-ᴄᴧsᴛ",
                callback_data="help_gcast",
                style=enums.ButtonStyle.PRIMARY,
            ),
        ],
        [
            InlineKeyboardButton(
                "ʙʟ-ᴄʜᴧᴛ",
                callback_data="help_blchat",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "ʙʟ-ᴜsᴇʀs",
                callback_data="help_blusers",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "ᴘɪɴɢ",
                callback_data="help_ping",
                style=enums.ButtonStyle.PRIMARY,
            ),
        ],
        [
            InlineKeyboardButton(
                "ᴘʟᴀʏ",
                callback_data="help_play",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "sᴘᴇᴇᴅ",
                callback_data="help_speed",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "ɪɴғᴏ",
                callback_data="help_info",
                style=enums.ButtonStyle.PRIMARY,
            ),
        ],
        [
            InlineKeyboardButton(
                "⌯ ᴄʟᴏsᴇ ⌯",
                callback_data="close_help",
                style=enums.ButtonStyle.DANGER,
            ),
        ],
    ])

    photo = random.choice(config.START_PHOTOS)

    caption = (
        rich_heading("📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ", level=3)
        + rich_img(photo)
        + rich_note(
    "ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴩ<br><br>"
    "ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ"
        )
        + rich_details(
            "✦ ʜᴇʟᴘ ғᴇᴀᴛᴜʀᴇs ✦",
            rich_table(
                ["ғᴇᴀᴛᴜʀᴇ", "ᴅᴇᴛᴀɪʟs"],
                [
                    (
                        "✉️ ʜᴇʟᴘ ᴍᴇɴᴜ",
                        "ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /",
                    ),
                ],
            ),
            open=True,
        )
        + rich_note(
            "ᴘᴏᴡᴇʀᴇᴅ ʙʏ » "
            "<a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>"
        )
        
    )

    await rich_send(
        bot,
        message.chat.id,
        caption,
        reply_markup=kb,
    )
