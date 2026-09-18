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
    ChosenInlineResult,
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
            return T
... 
