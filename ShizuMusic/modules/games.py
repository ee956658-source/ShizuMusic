# --------------------------------------------------------------------------------
#  ShizuMusic © 2026 — Games Module (NEW)
#  Inline multiplayer games feature
#  Does NOT touch any music / player logic
# --------------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import random
import string
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from ShizuMusic import bot

# ── Game storage (in-memory) ───────────────────────────────────────────────────
# key = game_id
GAMES: Dict[str, "BaseGame"] = {}
GAME_TTL = 3600  # seconds


def _uid(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _cleanup_old_games() -> None:
    now = time.time()
    dead = [gid for gid, g in GAMES.items() if now - g.created_at > GAME_TTL]
    for gid in dead:
        GAMES.pop(gid, None)


# ══════════════════════════════════════════════════════════════════════════════
# BASE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BaseGame:
    game_id: str
    game_type: str
    created_at: float = field(default_factory=time.time)
    player1: Optional[int] = None
    player1_name: str = ""
    player2: Optional[int] = None
    player2_name: str = ""
    turn: int = 1  # 1 or 2
    status: str = "waiting"  # waiting | playing | finished
    winner: Optional[int] = None  # user_id or 0 for draw

    def is_player(self, uid: int) -> bool:
        return uid in (self.player1, self.player2)

    def opponent(self, uid: int) -> Optional[int]:
        if uid == self.player1:
            return self.player2
        if uid == self.player2:
            return self.player1
        return None

    def current_player(self) -> Optional[int]:
        return self.player1 if self.turn == 1 else self.player2

    def name_of(self, uid: Optional[int]) -> str:
        if uid == self.player1:
            return self.player1_name or "Player 1"
        if uid == self.player2:
            return self.player2_name or "Player 2"
        return "—"


# ══════════════════════════════════════════════════════════════════════════════
# 1. TIC-TAC-TOE
# ══════════════════════════════════════════════════════════════════════════════

class TicTacToe(BaseGame):
    def __init__(self, game_id: str):
        super().__init__(game_id=game_id, game_type="ttt")
        self.board: List[str] = [" "] * 9  # 0-8

    def mark(self) -> str:
        return "❌" if self.turn == 1 else "⭕"

    def make_move(self, pos: int, uid: int) -> Tuple[bool, str]:
        if self.status != "playing":
            return False, "Game not active"
        if uid != self.current_player():
            return False, "Not your turn"
        if pos < 0 or pos > 8 or self.board[pos] != " ":
            return False, "Invalid move"
        self.board[pos] = self.mark()
        if self._check_win(self.mark()):
            self.status = "finished"
            self.winner = uid
            return True, "win"
        if " " not in self.board:
            self.status = "finished"
            self.winner = 0
            return True, "draw"
        self.turn = 2 if self.turn == 1 else 1
        return True, "ok"

    def _check_win(self, mark: str) -> bool:
        lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        ]
        return any(self.board[a] == self.board[b] == self.board[c] == mark for a, b, c in lines)

    def keyboard(self) -> InlineKeyboardMarkup:
        rows = []
        for r in range(3):
            btns = []
            for c in range(3):
                i = r * 3 + c
                label = self.board[i] if self.board[i] != " " else "▫️"
                btns.append(
                    InlineKeyboardButton(
                        label,
                        callback_data=f"g:ttt:{self.game_id}:{i}",
                    )
                )
            rows.append(btns)
        if self.status == "waiting":
            rows.append([
                InlineKeyboardButton("🎮 Join Game", callback_data=f"g:join:{self.game_id}")
            ])
        return InlineKeyboardMarkup(rows)

    def text(self) -> str:
        p1 = self.player1_name or "Waiting…"
        p2 = self.player2_name or "Waiting…"
        if self.status == "waiting":
            return (
                f"❌⭕ <b>Tic-Tac-Toe</b>\n\n"
                f"Player 1: {p1}\n"
                f"Player 2: {p2}\n\n"
                f"Waiting for opponent to join…"
            )
        if self.status == "finished":
            if self.winner == 0:
                result = "🤝 It's a <b>Draw</b>!"
            else:
                result = f"🏆 Winner: <b>{self.name_of(self.winner)}</b>"
            return (
                f"❌⭕ <b>Tic-Tac-Toe</b> — Finished\n\n"
                f"❌ {self.player1_name}\n"
                f"⭕ {self.player2_name}\n\n"
                f"{result}"
            )
        turn_name = self.name_of(self.current_player())
        return (
            f"❌⭕ <b>Tic-Tac-Toe</b>\n\n"
            f"❌ {self.player1_name}\n"
            f"⭕ {self.player2_name}\n\n"
            f"Turn: <b>{turn_name}</b> ({self.mark()})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. CONNECT FOUR
# ══════════════════════════════════════════════════════════════════════════════

class ConnectFour(BaseGame):
    ROWS = 6
    COLS = 7

    def __init__(self, game_id: str):
        super().__init__(game_id=game_id, game_type="c4")
        self.board: List[List[str]] = [[" " for _ in range(self.COLS)] for _ in range(self.ROWS)]

    def mark(self) -> str:
        return "🔴" if self.turn == 1 else "🟡"

    def make_move(self, col: int, uid: int) -> Tuple[bool, str]:
        if self.status != "playing":
            return False, "Game not active"
        if uid != self.current_player():
            return False, "Not your turn"
        if col < 0 or col >= self.COLS:
            return False, "Invalid column"
        # find lowest empty row
        row = None
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == " ":
                row = r
                break
        if row is None:
            return False, "Column full"
        self.board[row][col] = self.mark()
        if self._check_win(row, col, self.mark()):
            self.status = "finished"
            self.winner = uid
            return True, "win"
        if all(self.board[0][c] != " " for c in range(self.COLS)):
            self.status = "finished"
            self.winner = 0
            return True, "draw"
        self.turn = 2 if self.turn == 1 else 1
        return True, "ok"

    def _check_win(self, row: int, col: int, mark: str) -> bool:
        def count(dr: int, dc: int) -> int:
            n = 0
            r, c = row + dr, col + dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == mark:
                n += 1
                r += dr
                c += dc
            return n

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            if 1 + count(dr, dc) + count(-dr, -dc) >= 4:
                return True
        return False

    def keyboard(self) -> InlineKeyboardMarkup:
        # column drop buttons
        drop = [
            InlineKeyboardButton(str(c + 1), callback_data=f"g:c4:{self.game_id}:{c}")
            for c in range(self.COLS)
        ]
        rows = [drop]
        # board display as text buttons (read-only look)
        for r in range(self.ROWS):
            row_btns = []
            for c in range(self.COLS):
                cell = self.board[r][c]
                label = cell if cell != " " else "⚪"
                row_btns.append(
                    InlineKeyboardButton(label, callback_data=f"g:noop:{self.game_id}")
                )
            rows.append(row_btns)
        if self.status == "waiting":
            rows.append([
                InlineKeyboardButton("🎮 Join Game", callback_data=f"g:join:{self.game_id}")
            ])
        return InlineKeyboardMarkup(rows)

    def text(self) -> str:
        p1 = self.player1_name or "Waiting…"
        p2 = self.player2_name or "Waiting…"
        if self.status == "waiting":
            return (
                f"🔴🟡 <b>Connect Four</b>\n\n"
                f"Player 1: {p1}\n"
                f"Player 2: {p2}\n\n"
                f"Waiting for opponent to join…"
            )
        if self.status == "finished":
            if self.winner == 0:
                result = "🤝 It's a <b>Draw</b>!"
            else:
                result = f"🏆 Winner: <b>{self.name_of(self.winner)}</b>"
            return (
                f"🔴🟡 <b>Connect Four</b> — Finished\n\n"
                f"🔴 {self.player1_name}\n"
                f"🟡 {self.player2_name}\n\n"
                f"{result}"
            )
        turn_name = self.name_of(self.current_player())
        return (
            f"🔴🟡 <b>Connect Four</b>\n\n"
            f"🔴 {self.player1_name}\n"
            f"🟡 {self.player2_name}\n\n"
            f"Turn: <b>{turn_name}</b> ({self.mark()})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 3. ROCK-PAPER-SCISSORS
# ══════════════════════════════════════════════════════════════════════════════

RPS_CHOICES = {
    "rock": "🪨 Rock",
    "paper": "📄 Paper",
    "scissors": "✂️ Scissors",
}

RPS_WINS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}


class RockPaperScissors(BaseGame):
    def __init__(self, game_id: str):
        super().__init__(game_id=game_id, game_type="rps")
        self.choice1: Optional[str] = None
        self.choice2: Optional[str] = None

    def make_choice(self, choice: str, uid: int) -> Tuple[bool, str]:
        if self.status != "playing":
            return False, "Game not active"
        if choice not in RPS_CHOICES:
            return False, "Invalid"
        if uid == self.player1:
            if self.choice1:
                return False, "Already chosen"
            self.choice1 = choice
        elif uid == self.player2:
            if self.choice2:
                return False, "Already chosen"
            self.choice2 = choice
        else:
            return False, "Not a player"
        if self.choice1 and self.choice2:
            self.status = "finished"
            if self.choice1 == self.choice2:
                self.winner = 0
            elif RPS_WINS[self.choice1] == self.choice2:
                self.winner = self.player1
            else:
                self.winner = self.player2
            return True, "done"
        return True, "ok"

    def keyboard(self) -> InlineKeyboardMarkup:
        if self.status == "waiting":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Join Game", callback_data=f"g:join:{self.game_id}")]
            ])
        if self.status == "finished":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Play Again", callback_data=f"g:again:rps")]
            ])
        # show choices only if player hasn't chosen yet — but since it's shared message,
        # we always show buttons; make_choice guards duplicates
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🪨 Rock", callback_data=f"g:rps:{self.game_id}:rock"),
                InlineKeyboardButton("📄 Paper", callback_data=f"g:rps:{self.game_id}:paper"),
                InlineKeyboardButton("✂️ Scissors", callback_data=f"g:rps:{self.game_id}:scissors"),
            ]
        ])

    def text(self) -> str:
        p1 = self.player1_name or "Waiting…"
        p2 = self.player2_name or "Waiting…"
        if self.status == "waiting":
            return (
                f"🪨📄✂️ <b>Rock-Paper-Scissors</b>\n\n"
                f"Player 1: {p1}\n"
                f"Player 2: {p2}\n\n"
                f"Waiting for opponent to join…"
            )
        if self.status == "finished":
            c1 = RPS_CHOICES.get(self.choice1 or "", "—")
            c2 = RPS_CHOICES.get(self.choice2 or "", "—")
            if self.winner == 0:
                result = "🤝 It's a <b>Draw</b>!"
            else:
                result = f"🏆 Winner: <b>{self.name_of(self.winner)}</b>"
            return (
                f"🪨📄✂️ <b>Rock-Paper-Scissors</b> — Finished\n\n"
                f"{self.player1_name}: {c1}\n"
                f"{self.player2_name}: {c2}\n\n"
                f"{result}"
            )
        s1 = "✅ Chosen" if self.choice1 else "⏳ Choosing…"
        s2 = "✅ Chosen" if self.choice2 else "⏳ Choosing…"
        return (
            f"🪨📄✂️ <b>Rock-Paper-Scissors</b>\n\n"
            f"{self.player1_name}: {s1}\n"
            f"{self.player2_name}: {s2}\n\n"
            f"Both players — pick your move!"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. ROCK-PAPER-SCISSORS-LIZARD-SPOCK
# ══════════════════════════════════════════════════════════════════════════════

RPSLS_CHOICES = {
    "rock": "🪨 Rock",
    "paper": "📄 Paper",
    "scissors": "✂️ Scissors",
    "lizard": "🦎 Lizard",
    "spock": "🖖 Spock",
}

# what each choice beats
RPSLS_WINS = {
    "rock": {"scissors", "lizard"},
    "paper": {"rock", "spock"},
    "scissors": {"paper", "lizard"},
    "lizard": {"spock", "paper"},
    "spock": {"scissors", "rock"},
}


class RockPaperScissorsLizardSpock(BaseGame):
    def __init__(self, game_id: str):
        super().__init__(game_id=game_id, game_type="rpsls")
        self.choice1: Optional[str] = None
        self.choice2: Optional[str] = None

    def make_choice(self, choice: str, uid: int) -> Tuple[bool, str]:
        if self.status != "playing":
            return False, "Game not active"
        if choice not in RPSLS_CHOICES:
            return False, "Invalid"
        if uid == self.player1:
            if self.choice1:
                return False, "Already chosen"
            self.choice1 = choice
        elif uid == self.player2:
            if self.choice2:
                return False, "Already chosen"
            self.choice2 = choice
        else:
            return False, "Not a player"
        if self.choice1 and self.choice2:
            self.status = "finished"
            if self.choice1 == self.choice2:
                self.winner = 0
            elif self.choice2 in RPSLS_WINS[self.choice1]:
                self.winner = self.player1
            else:
                self.winner = self.player2
            return True, "done"
        return True, "ok"

    def keyboard(self) -> InlineKeyboardMarkup:
        if self.status == "waiting":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Join Game", callback_data=f"g:join:{self.game_id}")]
            ])
        if self.status == "finished":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Play Again", callback_data=f"g:again:rpsls")]
            ])
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🪨", callback_data=f"g:rpsls:{self.game_id}:rock"),
                InlineKeyboardButton("📄", callback_data=f"g:rpsls:{self.game_id}:paper"),
                InlineKeyboardButton("✂️", callback_data=f"g:rpsls:{self.game_id}:scissors"),
            ],
            [
                InlineKeyboardButton("🦎 Lizard", callback_data=f"g:rpsls:{self.game_id}:lizard"),
                InlineKeyboardButton("🖖 Spock", callback_data=f"g:rpsls:{self.game_id}:spock"),
            ],
        ])

    def text(self) -> str:
        p1 = self.player1_name or "Waiting…"
        p2 = self.player2_name or "Waiting…"
        if self.status == "waiting":
            return (
                f"🪨📄✂️🦎🖖 <b>RPS Lizard-Spock</b>\n\n"
                f"Player 1: {p1}\n"
                f"Player 2: {p2}\n\n"
                f"Waiting for opponent to join…"
            )
        if self.status == "finished":
            c1 = RPSLS_CHOICES.get(self.choice1 or "", "—")
            c2 = RPSLS_CHOICES.get(self.choice2 or "", "—")
            if self.winner == 0:
                result = "🤝 It's a <b>Draw</b>!"
            else:
                result = f"🏆 Winner: <b>{self.name_of(self.winner)}</b>"
            return (
                f"🪨📄✂️🦎🖖 <b>RPS Lizard-Spock</b> — Finished\n\n"
                f"{self.player1_name}: {c1}\n"
                f"{self.player2_name}: {c2}\n\n"
                f"{result}"
            )
        s1 = "✅ Chosen" if self.choice1 else "⏳ Choosing…"
        s2 = "✅ Chosen" if self.choice2 else "⏳ Choosing…"
        return (
            f"🪨📄✂️🦎🖖 <b>RPS Lizard-Spock</b>\n\n"
            f"{self.player1_name}: {s1}\n"
            f"{self.player2_name}: {s2}\n\n"
            f"Both players — pick your move!"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 5. RUSSIAN ROULETTE
# ══════════════════════════════════════════════════════════════════════════════

class RussianRoulette(BaseGame):
    def __init__(self, game_id: str):
        super().__init__(game_id=game_id, game_type="rr")
        self.chambers = [False] * 6
        self.chambers[random.randint(0, 5)] = True  # one bullet
        self.current_chamber = 0
        self.alive = {1: True, 2: True}
        self.last_result = ""

    def pull(self, uid: int) -> Tuple[bool, str]:
        if self.status != "playing":
            return False, "Game not active"
        if uid != self.current_player():
            return False, "Not your turn"
        bullet = self.chambers[self.current_chamber]
        self.current_chamber += 1
        if bullet:
            # dead
            slot = 1 if uid == self.player1 else 2
            self.alive[slot] = False
            self.status = "finished"
            self.winner = self.player2 if uid == self.player1 else self.player1
            self.last_result = f"💥 BANG! {self.name_of(uid)} is out!"
            return True, "dead"
        self.last_result = f"😅 Click… {self.name_of(uid)} survived!"
        # next turn
        self.turn = 2 if self.turn == 1 else 1
        if self.current_chamber >= 6:
            # rare: all empty somehow — reshape
            self.chambers = [False] * 6
            self.chambers[random.randint(0, 5)] = True
            self.current_chamber = 0
        return True, "safe"

    def keyboard(self) -> InlineKeyboardMarkup:
        if self.status == "waiting":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Join Game", callback_data=f"g:join:{self.game_id}")]
            ])
        if self.status == "finished":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Play Again", callback_data=f"g:again:rr")]
            ])
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔫 Pull Trigger", callback_data=f"g:rr:{self.game_id}:pull")]
        ])

    def text(self) -> str:
        p1 = self.player1_name or "Waiting…"
        p2 = self.player2_name or "Waiting…"
        if self.status == "waiting":
            return (
                f"🔫 <b>Russian Roulette</b>\n\n"
                f"Player 1: {p1}\n"
                f"Player 2: {p2}\n\n"
                f"Waiting for opponent to join…"
            )
        if self.status == "finished":
            return (
                f"🔫 <b>Russian Roulette</b> — Finished\n\n"
                f"{self.player1_name} vs {self.player2_name}\n\n"
                f"{self.last_result}\n"
                f"🏆 Winner: <b>{self.name_of(self.winner)}</b>"
            )
        turn_name = self.name_of(self.current_player())
        left = 6 - self.current_chamber
        return (
            f"🔫 <b>Russian Roulette</b>\n\n"
            f"{self.player1_name} vs {self.player2_name}\n\n"
            f"Chambers left: {left}/6\n"
            f"{self.last_result}\n\n"
            f"Turn: <b>{turn_name}</b>"
        )


# ══════════════════════════════════════════════════════════════════════════════
# FACTORY
# ══════════════════════════════════════════════════════════════════════════════

GAME_CLASSES = {
    "ttt": TicTacToe,
    "c4": ConnectFour,
    "rps": RockPaperScissors,
    "rpsls": RockPaperScissorsLizardSpock,
    "rr": RussianRoulette,
}

GAME_TITLES = {
    "ttt": "❌⭕ Tic-Tac-Toe",
    "c4": "🔴🟡 Connect Four",
    "rps": "🪨📄✂️ Rock-Paper-Scissors",
    "rpsls": "🦎🖖 RPS Lizard-Spock",
    "rr": "🔫 Russian Roulette",
}


def create_game(game_type: str) -> BaseGame:
    cls = GAME_CLASSES[game_type]
    gid = _uid()
    game = cls(gid)
    GAMES[gid] = game
    return game


# ══════════════════════════════════════════════════════════════════════════════
# INLINE QUERY — @bot menu
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_inline_query()
async def games_inline_query(_, query: InlineQuery) -> None:
    try:
        _cleanup_old_games()
        user = query.from_user
        if not user:
            await query.answer(
                results=[],
                cache_time=1,
                is_personal=True,
                switch_pm_text="Open bot first",
                switch_pm_parameter="start",
            )
            return

        results = []
        for gtype, title in GAME_TITLES.items():
            try:
                game = create_game(gtype)
                game.player1 = user.id
                game.player1_name = (user.first_name or "Player 1")[:32]
                game.status = "waiting"

                results.append(
                    InlineQueryResultArticle(
                        id=f"g_{game.game_id}",
                        title=title,
                        description="Tap to start • Multiplayer",
                        input_message_content=InputTextMessageContent(
                            message_text=game.text(),
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        ),
                        reply_markup=game.keyboard(),
                    )
                )
            except Exception:
                continue

        if not results:
            # fallback so Telegram never spins forever
            results.append(
                InlineQueryResultArticle(
                    id=f"err_{_uid(4)}",
                    title="Games unavailable",
                    description="Try again in a moment",
                    input_message_content=InputTextMessageContent(
                        message_text="Games temporarily unavailable. Please try again.",
                    ),
                )
            )

        await query.answer(results, cache_time=1, is_personal=True)

    except Exception:
        # last resort — always answer something
        try:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id=f"err_{_uid(4)}",
                        title="Error loading games",
                        description="Please try again",
                        input_message_content=InputTextMessageContent(
                            message_text="Could not load games. Try again.",
                        ),
                    )
                ],
                cache_time=1,
                is_personal=True,
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACK HANDLER (games only) — high priority so it runs before music callbacks
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_callback_query(filters.regex(r"^g:"), group=-2)
async def games_callback(_, cbq: CallbackQuery) -> None:
    data = cbq.data or ""
    user = cbq.from_user
    if not user:
        await cbq.answer()
        return

    parts = data.split(":")
    # g:action:...
    if len(parts) < 2:
        await cbq.answer()
        return

    action = parts[1]

    # ── noop (board cells that do nothing) ────────────────────────────────────
    if action == "noop":
        await cbq.answer()
        return

    # ── Play Again (create fresh lobby of same type) ──────────────────────────
    if action == "again":
        if len(parts) < 3:
            await cbq.answer()
            return
        gtype = parts[2]
        if gtype not in GAME_CLASSES:
            await cbq.answer("Unknown game", show_alert=True)
            return
        game = create_game(gtype)
        game.player1 = user.id
        game.player1_name = user.first_name or "Player 1"
        game.status = "waiting"
        try:
            await cbq.edit_message_text(
                game.text(),
                parse_mode=ParseMode.HTML,
                reply_markup=game.keyboard(),
            )
        except Exception:
            pass
        await cbq.answer("New game created!")
        return

    # ── Join ──────────────────────────────────────────────────────────────────
    if action == "join":
        if len(parts) < 3:
            await cbq.answer()
            return
        gid = parts[2]
        game = GAMES.get(gid)
        if not game:
            await cbq.answer("Game expired or not found", show_alert=True)
            return
        if game.status != "waiting":
            await cbq.answer("Game already started", show_alert=True)
            return
        if game.player1 == user.id:
            await cbq.answer("You are already Player 1", show_alert=True)
            return
        game.player2 = user.id
        game.player2_name = user.first_name or "Player 2"
        game.status = "playing"
        game.turn = 1
        try:
            await cbq.edit_message_text(
                game.text(),
                parse_mode=ParseMode.HTML,
                reply_markup=game.keyboard(),
            )
        except Exception:
            pass
        await cbq.answer("Joined! Game started.")
        return

    # ── Game moves ────────────────────────────────────────────────────────────
    if len(parts) < 3:
        await cbq.answer()
        return

    gtype = action
    gid = parts[2]
    game = GAMES.get(gid)
    if not game:
        await cbq.answer("Game expired", show_alert=True)
        return
    if not game.is_player(user.id):
        await cbq.answer("You are not in this game", show_alert=True)
        return

    ok = False
    msg = ""

    if gtype == "ttt" and len(parts) >= 4:
        try:
            pos = int(parts[3])
        except ValueError:
            await cbq.answer("Invalid", show_alert=True)
            return
        ok, msg = game.make_move(pos, user.id)  # type: ignore

    elif gtype == "c4" and len(parts) >= 4:
        try:
            col = int(parts[3])
        except ValueError:
            await cbq.answer("Invalid", show_alert=True)
            return
        ok, msg = game.make_move(col, user.id)  # type: ignore

    elif gtype == "rps" and len(parts) >= 4:
        choice = parts[3]
        ok, msg = game.make_choice(choice, user.id)  # type: ignore

    elif gtype == "rpsls" and len(parts) >= 4:
        choice = parts[3]
        ok, msg = game.make_choice(choice, user.id)  # type: ignore

    elif gtype == "rr" and len(parts) >= 4 and parts[3] == "pull":
        ok, msg = game.pull(user.id)  # type: ignore

    else:
        await cbq.answer()
        return

    if not ok:
        await cbq.answer(msg, show_alert=True)
        return

    # refresh board
    try:
        await cbq.edit_message_text(
            game.text(),
            parse_mode=ParseMode.HTML,
            reply_markup=game.keyboard(),
        )
    except Exception:
        pass

    if msg in ("win", "draw", "dead", "done"):
        await cbq.answer("Game over!")
    else:
        await cbq.answer()
