"""
Connect Four: 6 rows × 7 columns. Two players drop pieces; first to get 4 in a row wins.
State is an immutable tuple of 42 cells (row-major, row 0 = top): 0 = empty, 1 = player 0, 2 = player 1.
Actions are column indices 0–6.
"""

from __future__ import annotations

ROWS = 6
COLS = 7

# Board: flat tuple of ROWS*COLS ints, index = row*COLS + col
Board = tuple[int, ...]


def initial_state() -> Board:
    return (0,) * (ROWS * COLS)


def get_current_player_from_board(board: Board) -> int:
    n = sum(1 for c in board if c != 0)
    return 0 if n % 2 == 0 else 1


def _count_in_column(board: Board, col: int) -> int:
    return sum(1 for r in range(ROWS) if board[r * COLS + col] != 0)


def _drop_row(board: Board, col: int) -> int:
    """Row index where a drop in col would land (0=top, 5=bottom)."""
    count = _count_in_column(board, col)
    return ROWS - 1 - count  # bottom row is ROWS-1


def winner(board: Board) -> int | None:
    """Return 1 or 2 if that player has four in a row, else None."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            a = board[r * COLS + c]
            if a and a == board[r * COLS + c + 1] == board[r * COLS + c + 2] == board[r * COLS + c + 3]:
                return a
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            a = board[r * COLS + c]
            if a and a == board[(r + 1) * COLS + c] == board[(r + 2) * COLS + c] == board[(r + 3) * COLS + c]:
                return a
    # Diagonal \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            a = board[r * COLS + c]
            if a and a == board[(r + 1) * COLS + c + 1] == board[(r + 2) * COLS + c + 2] == board[(r + 3) * COLS + c + 3]:
                return a
    # Diagonal /
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            a = board[r * COLS + c]
            if a and a == board[(r - 1) * COLS + c + 1] == board[(r - 2) * COLS + c + 2] == board[(r - 3) * COLS + c + 3]:
                return a
    return None


class ConnectFour:
    def get_current_player(self, state: Board) -> int:
        return get_current_player_from_board(state)

    def get_legal_actions(self, state: Board) -> list[int]:
        if self.is_terminal(state):
            return []
        return [c for c in range(COLS) if _count_in_column(state, c) < ROWS]

    def apply_action(self, state: Board, action: int) -> Board:
        row = _drop_row(state, action)
        player = self.get_current_player(state)
        cell_value = player + 1  # 1 or 2
        i = row * COLS + action
        board = list(state)
        board[i] = cell_value
        return tuple(board)

    def is_terminal(self, state: Board) -> bool:
        if winner(state) is not None:
            return True
        return all(state[r * COLS + c] != 0 for r in range(ROWS) for c in range(COLS))

    def get_outcome(self, state: Board) -> dict[int, float]:
        w = winner(state)
        if w is not None:
            return {0: 1.0 if w == 1 else 0.0, 1: 1.0 if w == 2 else 0.0}
        return {0: 0.5, 1: 0.5}


def format_board(board: Board) -> str:
    chars = {0: ".", 1: "X", 2: "O"}
    lines = [
        " ".join(chars[board[r * COLS + c]] for c in range(COLS))
        for r in range(ROWS)
    ]
    lines.append(" ".join(str(c + 1) for c in range(COLS)))
    return "\n".join(lines)
