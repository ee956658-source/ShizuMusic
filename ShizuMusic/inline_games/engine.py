import asyncio
import html
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

# In-memory sessions are intentionally isolated from the music system.
# A later persistence adapter can store these in MongoDB without changing handlers.
SESSIONS: Dict[str, "Session"] = {}
LOCK = asyncio.Lock()

GAMES = {
    "ttt": ("❌ Tic-Tac-Toe", "Classic 3x3 two-player game."),
    "ttf": ("🔢 Tic-Tac-Four", "Connect four marks in a row on a 4x4 board."),
    "exo": ("🐘 Elephant XO", "A two-player XO variant."),
    "c4": ("🔵 Connect Four", "Drop pieces and connect four."),
    "rps": ("✊ Rock-Paper-Scissors", "Challenge another player."),
    "rpsls": ("🖖 RPS-Lizard-Spock", "The expanded rock-paper-scissors game."),
    "rr": ("🎯 Russian Roulette", "A luck-based multiplayer mini-game."),
    "checkers": ("♟ Checkers", "Classic checkers board game."),
    "pool": ("🎱 Pool Checkers", "Pool-checkers variant."),
}


def menu_results():
    out = []
    for code, (title, desc) in GAMES.items():
        out.append(
            InlineQueryResultArticle(
                id=f"yor-game-{code}",
                title=title,
                description=desc,
                input_message_content=InputTextMessageContent(
                    message_text=f"<b>{html.escape(title)}</b>\n\n🔒 Game session not started.\nPress <b>Start game</b> to create a session.",
                    parse_mode="html",
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🎮 Start game", callback_data=f"ig:new:{code}")]]
                ),
            )
        )
    return out


@dataclass
class Session:
    code: str
    game: str
    created: float = field(default_factory=time.time)
    players: list = field(default_factory=list)
    turn: int = 0
    board: list = field(default_factory=list)
    moves: dict = field(default_factory=dict)
    finished: bool = False


def _name(user):
    return html.escape(user.first_name or user.username or str(user.id))


def _user_key(user):
    return int(user.id)


def _session_key(inline_message_id, code):
    return f"{inline_message_id}:{code}"


def _ttt_board(session):
    b = session.board or [" "] * 9
    rows = []
    for i in range(0, 9, 3):
        rows.append(" | ".join(b[i:i + 3]))
    return "\n---------\n".join(rows)


def _connect4_board(session):
    b = session.board or [" "] * 42
    rows = []
    for i in range(0, 42, 7):
        rows.append("│" + "│".join(b[i:i + 7]) + "│")
    return "\n".join(rows)


def _win_ttt(b, mark):
    return any(all(b[i] == mark for i in line) for line in ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)))


def _win_c4(b, mark):
    for r in range(6):
        for c in range(7):
            i = r * 7 + c
            if c <= 3 and all(b[i + j] == mark for j in range(4)): return True
            if r <= 2 and all(b[i + j * 7] == mark for j in range(4)): return True
            if r <= 2 and c <= 3 and all(b[i + j * 8] == mark for j in range(4)): return True
            if r <= 2 and c >= 3 and all(b[i + j * 6] == mark for j in range(4)): return True
    return False


def _keyboard(session_key, session):
    if session.game == "ttt":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i + 1), callback_data=f"ig:mv:{session_key}:{i}") for i in range(3)],
            [InlineKeyboardButton(str(i + 4), callback_data=f"ig:mv:{session_key}:{i}") for i in range(3, 6)],
            [InlineKeyboardButton(str(i + 7), callback_data=f"ig:mv:{session_key}:{i}") for i in range(6, 9)],
            [InlineKeyboardButton("🔄 New game", callback_data=f"ig:new:{session.game}")],
        ])
    if session.game == "c4":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i + 1), callback_data=f"ig:mv:{session_key}:{i}") for i in range(7)],
            [InlineKeyboardButton("🔄 New game", callback_data=f"ig:new:{session.game}")],
        ])
    if session.game == "rps":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✊ Rock", callback_data=f"ig:mv:{session_key}:rock"), InlineKeyboardButton("📄 Paper", callback_data=f"ig:mv:{session_key}:paper")],
            [InlineKeyboardButton("✂️ Scissors", callback_data=f"ig:mv:{session_key}:scissors")],
            [InlineKeyboardButton("🔄 New game", callback_data=f"ig:new:{session.game}")],
        ])
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 New game", callback_data=f"ig:new:{session.game}")]])


def _render(key, s):
    title = GAMES[s.game][0]
    if s.game == "ttt":
        board = _ttt_board(s)
        rules = "Players: ❌ and ⭕. Choose a numbered cell."
    elif s.game == "c4":
        board = _connect4_board(s)
        rules = "Players: 🔴 and 🟡. Choose a column."
    elif s.game == "rps":
        board = "Moves are hidden until both players choose."
        rules = "Players choose Rock, Paper or Scissors."
    else:
        board = "This game module is reserved for the next game-engine phase."
        rules = "The menu and inline session system are already installed."
    players = ", ".join(f"{i+1}. {p['name']}" for i, p in enumerate(s.players)) or "Nobody yet"
    return f"<b>{html.escape(title)}</b>\n\n{board}\n\n👥 <b>Players:</b> {players}\n\nℹ️ {rules}", _keyboard(key, s)


async def start_session(query, code):
    key = _session_key(query.inline_message_id, code)
    async with LOCK:
        s = Session(code=code, game=code)
        SESSIONS[key] = s
        s.players.append({"id": _user_key(query.from_user), "name": _name(query.from_user)})
        if code == "ttt": s.board = [" "] * 9
        elif code == "c4": s.board = [" "] * 42
        text, markup = _render(key, s)
    return key, text, markup


async def handle_move(query, key, move):
    async with LOCK:
        s = SESSIONS.get(key)
        if not s:
            return None, "❌ This game session has expired."
        if s.finished:
            return None, "❌ This game has already finished."
        uid = _user_key(query.from_user)
        if not any(p["id"] == uid for p in s.players):
            if len(s.players) >= 2:
                return None, "❌ This game already has two players."
            s.players.append({"id": uid, "name": _name(query.from_user)})
        if len(s.players) < 2:
            text, markup = _render(key, s)
            return (text, markup), "⏳ Waiting for a second player."
        if s.game == "ttt":
            if s.players[s.turn % 2]["id"] != uid:
                return None, "⏳ It is the other player's turn."
            try: idx = int(move)
            except ValueError: return None, "❌ Invalid move."
            if idx < 0 or idx >= 9 or s.board[idx] != " ": return None, "❌ That cell is not available."
            mark = "❌" if s.turn % 2 == 0 else "⭕"
            s.board[idx] = mark; s.turn += 1
            if _win_ttt(s.board, mark): s.finished = True; result = f"🏆 {s.players[(s.turn-1)%2]['name']} wins!"
            elif " " not in s.board: s.finished = True; result = "🤝 Draw!"
            else: result = ""
        elif s.game == "c4":
            if s.players[s.turn % 2]["id"] != uid: return None, "⏳ It is the other player's turn."
            col = int(move)
            if col < 0 or col >= 7: return None, "❌ Invalid column."
            row = next((r for r in range(5, -1, -1) if s.board[r*7+col] == " "), None)
            if row is None: return None, "❌ That column is full."
            mark = "🔴" if s.turn % 2 == 0 else "🟡"; s.board[row*7+col] = mark; s.turn += 1
            if _win_c4(s.board, mark): s.finished = True; result = f"🏆 {s.players[(s.turn-1)%2]['name']} wins!"
            elif " " not in s.board: s.finished = True; result = "🤝 Draw!"
            else: result = ""
        elif s.game == "rps":
            if uid not in [p["id"] for p in s.players]: return None, "❌ Join the game first."
            s.moves[uid] = move
            if len(s.moves) < 2:
                text, markup = _render(key, s); return (text, markup), "⏳ Waiting for the other player's move."
            vals = list(s.moves.values()); a, b = vals[0], vals[1]
            result = "🤝 Draw!" if a == b else ("🏆 Player 1 wins!" if (a,b) in (("rock","scissors"),("scissors","paper"),("paper","rock")) else "🏆 Player 2 wins!")
            s.finished = True
        else:
            return None, "ℹ️ This game is being added in the next engine phase."
        text, markup = _render(key, s)
        if result: text += f"\n\n<b>{result}</b>"
        return (text, markup), result or "✅ Move accepted."
