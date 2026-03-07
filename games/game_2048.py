"""
2048: 4×4 grid, slide tiles (up/down/left/right), merge equals, spawn 2 or 4 in random empty cell.
State = (board_16_tuple, turn). turn = "player" | "chance".
After each move, turn becomes "chance"; apply_action(state, None) returns list of (new_state, prob).
"""

from __future__ import annotations

import random
from typing import Any

from mcts.game import Game

SIZE = 4
CELLS = SIZE * SIZE

# Board: tuple of 16 ints (row-major), 0 = empty, else 2, 4, 8, ...
# State: (board, "player" | "chance")
Board = tuple[int, ...]
State = tuple[Board, str]

# Directions: 0=up, 1=right, 2=down, 3=left
DIRS = (0, 1, 2, 3)


def _empty_board() -> Board:
    return (0,) * CELLS


def _row(board: Board, r: int) -> tuple[int, ...]:
    return tuple(board[r * SIZE + c] for c in range(SIZE))


def _set_row(board: Board, r: int, row: tuple[int, ...]) -> Board:
    b = list(board)
    for c in range(SIZE):
        b[r * SIZE + c] = row[c]
    return tuple(b)


def _col(board: Board, c: int) -> tuple[int, ...]:
    return tuple(board[r * SIZE + c] for r in range(SIZE))


def _set_col(board: Board, c: int, col: tuple[int, ...]) -> Board:
    b = list(board)
    for r in range(SIZE):
        b[r * SIZE + c] = col[r]
    return tuple(b)


def _slide_row_left(row: tuple[int, ...]) -> tuple[int, ...]:
    """Collapse row left, merging equal adjacent tiles."""
    nonzeros = [x for x in row if x != 0]
    merged: list[int] = []
    i = 0
    while i < len(nonzeros):
        if i + 1 < len(nonzeros) and nonzeros[i] == nonzeros[i + 1]:
            merged.append(nonzeros[i] * 2)
            i += 2
        else:
            merged.append(nonzeros[i])
            i += 1
    return tuple(merged + [0] * (SIZE - len(merged)))


def _slide_row_right(row: tuple[int, ...]) -> tuple[int, ...]:
    rev = _slide_row_left(tuple(reversed(row)))
    return tuple(reversed(rev))


def _slide_left(board: Board) -> Board:
    out = list(board)
    for r in range(SIZE):
        row = _row(board, r)
        new_row = _slide_row_left(row)
        for c in range(SIZE):
            out[r * SIZE + c] = new_row[c]
    return tuple(out)


def _slide_right(board: Board) -> Board:
    out = list(board)
    for r in range(SIZE):
        row = _row(board, r)
        new_row = _slide_row_right(row)
        for c in range(SIZE):
            out[r * SIZE + c] = new_row[c]
    return tuple(out)


def _slide_up(board: Board) -> Board:
    out = list(board)
    for c in range(SIZE):
        col = _col(board, c)
        new_col = _slide_row_left(col)
        for r in range(SIZE):
            out[r * SIZE + c] = new_col[r]
    return tuple(out)


def _slide_down(board: Board) -> Board:
    out = list(board)
    for c in range(SIZE):
        col = _col(board, c)
        new_col = _slide_row_right(col)
        for r in range(SIZE):
            out[r * SIZE + c] = new_col[r]
    return tuple(out)


def _slide(board: Board, direction: int) -> Board:
    if direction == 0:
        return _slide_up(board)
    if direction == 1:
        return _slide_right(board)
    if direction == 2:
        return _slide_down(board)
    return _slide_left(board)


def _empty_indices(board: Board) -> list[int]:
    return [i for i in range(CELLS) if board[i] == 0]


def _place_tile(board: Board, index: int, value: int) -> Board:
    b = list(board)
    b[index] = value
    return tuple(b)


def initial_state(seed: int | None = None) -> State:
    """Start with two tiles (2 or 4) in random positions. seed for reproducibility."""
    rng = random.Random(seed)
    board = _empty_board()
    empties = list(range(CELLS))
    for _ in range(2):
        idx = rng.choice(empties)
        empties.remove(idx)
        board = _place_tile(board, idx, 2 if rng.random() < 0.9 else 4)
    return (board, "player")


class Game2048:
    def get_current_player(self, state: State) -> Any:
        return state[1]  # "player" or "chance"

    def get_legal_actions(self, state: State) -> list[Any]:
        board, turn = state
        if turn == "chance":
            return [None]  # apply_action(state, None) returns outcomes
        # Player: directions that actually change the board
        legal = []
        for d in DIRS:
            if _slide(board, d) != board:
                legal.append(d)
        return legal

    def apply_action(self, state: State, action: Any) -> Any:
        board, turn = state
        if turn == "chance":
            # Return list of (new_state, prob) for each possible spawn
            empties = _empty_indices(board)
            if not empties:
                return (board, "player")  # shouldn't happen
            outcomes: list[tuple[State, float]] = []
            n = len(empties)
            for idx in empties:
                outcomes.append((( _place_tile(board, idx, 2), "player"), 0.9 / n))
                outcomes.append((( _place_tile(board, idx, 4), "player"), 0.1 / n))
            return outcomes
        # Player move
        new_board = _slide(board, action)
        return (new_board, "chance")

    def is_terminal(self, state: State) -> bool:
        board, turn = state
        if turn == "chance":
            return False
        return len(self.get_legal_actions(state)) == 0

    def get_outcome(self, state: State) -> dict[int, float]:
        board, _ = state
        total = sum(board)
        # Normalize so MCTS maximizes score (cap at 1.0 for ~20k+ score)
        score = min(1.0, total / 20000.0)
        return {0: score}


def format_board_2048(state: State) -> str:
    board, turn = state
    lines = []
    for r in range(SIZE):
        row = [str(board[r * SIZE + c]) if board[r * SIZE + c] else "." for c in range(SIZE)]
        lines.append(" ".join(f"{x:>4}" for x in row))
    return "\n".join(lines)


def direction_name(d: int) -> str:
    return ("up", "right", "down", "left")[d]
