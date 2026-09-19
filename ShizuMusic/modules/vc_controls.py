from html import escape

from pyrogram import enums, filters
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall
from pyrogram.raw.types import InputGroupCall
from pyrogram.types import Message

from ShizuMusic import assistant, bot
from ShizuMusic.utils.assistant import try_join_assistant


async def _can_manage_vc(message: Message) -> bool:
    if not message.from_user:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status == enums.ChatMemberStatus.OWNER or bool(
            getattr(member.privileges, "can_manage_video_chats", False)
        )
    except Exception:
        return False


async def _active_call(chat_id: int):
    try:
        chat = await assistant.get_chat(chat_id)
        peer = await assistant.resolve_peer(chat_id)
        if chat.type == enums.ChatType.SUPERGROUP:
            result = await assistant.invoke(GetFullChannel(channel=peer))
        elif chat.type == enums.ChatType.GROUP:
            result = await assistant.invoke(GetFullChat(chat_id=chat_id))
        else:
            return None
        call = getattr(result.full_chat, "call", None)
        if call and hasattr(call, "id") and hasattr(call, "access_hash"):
            return InputGroupCall(id=call.id, access_hash=call.access_hash)
    except Exception:
        return None
    return None


@bot.on_message(filters.group & filters.command("vstart"))
async def vstart(_, message: Message):
    if not await _can_manage_vc(message):
        return await message.reply_text("❌ You need manage-video-chats permission.")
    try:
        status = await try_join_assistant(message.chat.id, message)
        if not status:
            return
        if await _active_call(message.chat.id):
            return await message.reply_text("ℹ️ A voice chat is already active.")
        await assistant.invoke(
            CreateGroupCall(
                peer=await assistant.resolve_peer(message.chat.id),
                random_id=__import__('random').randint(1, 2_147_483_647),
            )
        )
        await message.reply_text("🎙️ <b>Voice chat started.</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Failed to start VC: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)


@bot.on_message(filters.group & filters.command("vend"))
async def vend(_, message: Message):
    if not await _can_manage_vc(message):
        return await message.reply_text("❌ You need manage-video-chats permission.")
    try:
        call = await _active_call(message.chat.id)
        if not call:
            return await message.reply_text("ℹ️ No active voice chat found.")
        await assistant.invoke(DiscardGroupCall(call=call))
        await message.reply_text("🔕 <b>Voice chat ended.</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Failed to end VC: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)


@bot.on_message(filters.group & filters.command(["vcinfo", "vcmembers"]))
async def vcinfo(_, message: Message):
    if not await _can_manage_vc(message):
        return await message.reply_text("❌ You need manage-video-chats permission.")
    try:
        # PyTgCalls exposes its MTProto bridge internally.  This uses the same
        # participant API used by the Trebelx implementation without creating
        # a second call client or touching ShizuMusic's player.
        mtproto = getattr(call_py := __import__('ShizuMusic', fromlist=['call_py']), 'call_py')._app
        participants = await mtproto.get_group_call_participants(message.chat.id)
        if not participants:
            return await message.reply_text("🎙️ No active VC participants found.")
        lines = ["🎧 <b>VC Members</b>\n"]
        for p in participants:
            uid = getattr(p, "user_id", None)
            if not uid:
                continue
            try:
                user = await bot.get_users(uid)
                name = f'<a href="tg://user?id={uid}">{escape(user.first_name or "User")}</a>'
            except Exception:
                name = f"<code>{uid}</code>"
            muted = "🔇" if getattr(p, "muted", False) else "🎙️"
            volume = getattr(p, "volume", None)
            lines.append(f"{muted} {name}" + (f" · 🔊 {volume}" if volume is not None else ""))
        await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Failed to fetch VC info: <code>{escape(str(e))}</code>", parse_mode=enums.ParseMode.HTML)
