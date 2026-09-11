from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message
from pyrogram.raw.functions.phone import (
    CreateGroupCall,
    DiscardGroupCall,
)
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.types import InputGroupCall

import random
import config

from ShizuMusic import bot, assistant


async def is_admin_or_owner(message: Message) -> bool:
    if not message.from_user:
        return False

    if message.from_user.id == config.OWNER_ID:
        return True

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id,
        )

        return member.status in ("administrator", "owner")

    except Exception:
        return False


async def get_active_group_call(chat_id: int):
    try:
        chat = await assistant.get_chat(chat_id)
        peer = await assistant.resolve_peer(chat_id)

        if chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL):
            result = await assistant.invoke(
                GetFullChannel(
                    channel=peer,
                )
            )
        else:
            result = await assistant.invoke(
                GetFullChat(
                    chat_id=chat_id,
                )
            )

        call = getattr(result.full_chat, "call", None)

        if not call:
            return None

        if not hasattr(call, "id") or not hasattr(call, "access_hash"):
            return None

        return InputGroupCall(
            id=call.id,
            access_hash=call.access_hash,
        )

    except Exception:
        return None


@bot.on_message(
    filters.group
    & filters.command("vcstart")
)
async def vc_start(_, message: Message) -> None:

    if not await is_admin_or_owner(message):
        return

    chat_id = message.chat.id

    try:
        existing_call = await get_active_group_call(chat_id)

        if existing_call:
            return

        await assistant.invoke(
            CreateGroupCall(
                peer=await assistant.resolve_peer(chat_id),
                random_id=random.randint(10000, 999999999),
            )
        )

    except Exception:
        return

    try:
        await message.delete()
    except Exception:
        pass


@bot.on_message(
    filters.group
    & filters.command("vcend")
)
async def vc_end(_, message: Message) -> None:

    if not await is_admin_or_owner(message):
        return

    chat_id = message.chat.id

    try:
        call = await get_active_group_call(chat_id)

        if not call:
            return

        await assistant.invoke(
            DiscardGroupCall(
                call=call,
            )
        )

    except Exception:
        return

    try:
        await message.delete()
    except Exception:
        pass
