from pyrogram import filters
from pyrogram.types import CallbackQuery
from ShizuMusic import bot
from .engine import menu_results, start_session, handle_move


@bot.on_inline_query()
async def inline_games_query(_, query):
    try:
        await query.answer(menu_results(), cache_time=0, is_personal=True)
    except Exception:
        pass


@bot.on_callback_query(filters.regex(r"^ig:"))
async def inline_games_callback(_, query: CallbackQuery):
    data = query.data or ""
    try:
        if not query.inline_message_id:
            await query.answer("This game must be sent through inline mode.", show_alert=True)
            return
        parts = data.split(":", 3)
        if parts[1] == "new":
            code = parts[2]
            key, text, markup = await start_session(query, code)
            await bot.edit_message_text(inline_message_id=query.inline_message_id, text=text, reply_markup=markup, parse_mode="html")
            await query.answer("Game started! Share it with another player.")
            return
        if parts[1] == "mv":
            key, move = parts[2], parts[3]
            result, notice = await handle_move(query, key, move)
            if result:
                text, markup = result
                await bot.edit_message_text(inline_message_id=query.inline_message_id, text=text, reply_markup=markup, parse_mode="html")
            await query.answer(notice, show_alert=notice.startswith("❌"))
            return
        await query.answer("Unknown game action.", show_alert=True)
    except Exception as e:
        await query.answer("Game error. Please start a new game.", show_alert=True)
