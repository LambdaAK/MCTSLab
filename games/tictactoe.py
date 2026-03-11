"""
Tic-tac-toe: 3x3 board, two players (0 = X, 1 = O).
State is an immutable tuple of 9 cells: 0 = empty, 1 = X, 2 = O.
"""

from __future__ import annotations

import random
from typing import Any

from mcts.game import Game

# Board: tuple of 9 ints, 0 = empty, 1 = player 0 (X), 2 = player 1 (O)
Board = tuple[int, ...]

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def initial_state() -> Board:
    return (0,) * 9


def get_current_player_from_board(board: Board) -> int:
    """Player 0 moves first; alternate by counting pieces."""
    n0 = sum(1 for c in board if c == 1)
    n1 = sum(1 for c in board if c == 2)
    return 0 if n0 == n1 else 1


def winner(board: Board) -> int | None:
    """Return 1 or 2 if that player has three in a row, else None."""
    for line in WIN_LINES:
        a, b, c = board[line[0]], board[line[1]], board[line[2]]
        if a and a == b == c:
            return a
    return None


class TicTacToe:
    def get_current_player(self, state: Board) -> int:
        return get_current_player_from_board(state)

    def get_legal_actions(self, state: Board) -> list[int]:
        if self.is_terminal(state):
            return []
        return [i for i in range(9) if state[i] == 0]

    def apply_action(self, state: Board, action: int) -> Board:
        board = list(state)
        board[action] = self.get_current_player(state) + 1  # 1 or 2
        return tuple(board)

    def is_terminal(self, state: Board) -> bool:
        if winner(state) is not None:
            return True
        return 0 not in state

    def get_outcome(self, state: Board) -> dict[int, float]:
        w = winner(state)
        if w is not None:
            return {0: 1.0 if w == 1 else 0.0, 1: 1.0 if w == 2 else 0.0}
        return {0: 0.5, 1: 0.5}  # draw

    def rollout_action(self, state: Board, legal: list[int], rng: random.Random) -> int:
        player_val = self.get_current_player(state) + 1
        opp_val = 3 - player_val
        # Take an immediate win.
        for a in legal:
            b = list(state)
            b[a] = player_val
            b = tuple(b)
            for line in WIN_LINES:
                if b[line[0]] == b[line[1]] == b[line[2]] == player_val:
                    return a
        # Block an immediate opponent win.
        for a in legal:
            b = list(state)
            b[a] = opp_val
            b = tuple(b)
            for line in WIN_LINES:
                if b[line[0]] == b[line[1]] == b[line[2]] == opp_val:
                    return a
        return rng.choice(legal)


def format_board(board: Board) -> str:
    chars = {0: ".", 1: "X", 2: "O"}
    rows = [
        " ".join(chars[board[r * 3 + c]] for c in range(3))
        for r in range(3)
    ]
    return "\n".join(rows)
