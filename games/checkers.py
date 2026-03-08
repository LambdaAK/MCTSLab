"""
Checkers: 6×6 board (smaller than standard 8×8). Two players, diagonal moves, forced capture.
State = (board, turn). Board: flat tuple of 36 cells, 0=empty, 1=P0 man, 2=P0 king, 3=P1 man, 4=P1 king.
Only dark squares (r+c odd) are used. Actions are move paths: ((r0,c0), (r1,c1), ...).
"""

from __future__ import annotations

from typing import Any

from mcts.game import Game

ROWS = 6
COLS = 6
SIZE = ROWS * COLS

# Cell: 0=empty, 1=P0 man, 2=P0 king, 3=P1 man, 4=P1 king
Board = tuple[int, ...]
# Move: path of (r,c) positions from start to end
Move = tuple[tuple[int, int], ...]
State = tuple[Board, int]  # (board, current_player)


def _is_dark(r: int, c: int) -> bool:
    return (r + c) % 2 == 1


def _idx(r: int, c: int) -> int:
    return r * COLS + c


def _get(board: Board, r: int, c: int) -> int:
    if 0 <= r < ROWS and 0 <= c < COLS:
        return board[_idx(r, c)]
    return -1


def _set(board: Board, r: int, c: int, val: int) -> Board:
    i = _idx(r, c)
    b = list(board)
    b[i] = val
    return tuple(b)


def _is_player_piece(cell: int, player: int) -> bool:
    if player == 0:
        return cell in (1, 2)
    return cell in (3, 4)


def _is_opponent_piece(cell: int, player: int) -> bool:
    if player == 0:
        return cell in (3, 4)
    return cell in (1, 2)


def _is_king(cell: int) -> bool:
    return cell in (2, 4)


def _man_can_move_forward(r: int, c: int, dr: int, player: int) -> bool:
    """Man can only move in forward direction. P0 moves up (dr=1), P1 moves down (dr=-1)."""
    if player == 0:
        return dr > 0
    return dr < 0


def _get_capture_moves(
    board: Board, player: int, r: int, c: int, path: tuple[tuple[int, int], ...]
) -> list[Move]:
    """Find all capture sequences starting from (r,c). path = squares visited so far."""
    piece = _get(board, r, c)
    if piece == 0 or not _is_player_piece(piece, player):
        return []
    is_king = _is_king(piece)
    moves: list[Move] = []
    found_any = False

    for dr in (-1, 1):
        for dc in (-1, 1):
            if not is_king and not _man_can_move_forward(r, c, dr, player):
                continue
            mid_r, mid_c = r + dr, c + dc
            to_r, to_c = r + 2 * dr, c + 2 * dc
            if not (0 <= to_r < ROWS and 0 <= to_c < COLS):
                continue
            if (to_r, to_c) in path:
                continue
            mid_cell = _get(board, mid_r, mid_c)
            to_cell = _get(board, to_r, to_c)
            if _is_opponent_piece(mid_cell, player) and to_cell == 0:
                # Can jump
                new_board = board
                new_board = _set(new_board, r, c, 0)
                new_board = _set(new_board, mid_r, mid_c, 0)
                new_piece = piece
                if player == 0 and to_r == ROWS - 1:
                    new_piece = 2
                elif player == 1 and to_r == 0:
                    new_piece = 4
                new_board = _set(new_board, to_r, to_c, new_piece)
                new_path = path + ((to_r, to_c),)
                found_any = True
                # Continue jumping from new position
                further = _get_capture_moves(new_board, player, to_r, to_c, new_path)
                if further:
                    moves.extend(further)
                else:
                    moves.append(new_path)

    return moves


def _get_simple_moves(board: Board, player: int, r: int, c: int) -> list[Move]:
    """Non-capturing diagonal moves."""
    piece = _get(board, r, c)
    if piece == 0 or not _is_player_piece(piece, player):
        return []
    is_king = _is_king(piece)
    moves: list[Move] = []

    for dr in (-1, 1):
        for dc in (-1, 1):
            if not is_king and not _man_can_move_forward(r, c, dr, player):
                continue
            to_r, to_c = r + dr, c + dc
            if 0 <= to_r < ROWS and 0 <= to_c < COLS and _get(board, to_r, to_c) == 0:
                moves.append(((r, c), (to_r, to_c)))
    return moves


def _get_all_moves(board: Board, player: int) -> list[Move]:
    """All legal moves for player. Forced capture: if any capture exists, only captures are legal."""
    captures: list[Move] = []
    for r in range(ROWS):
        for c in range(COLS):
            if _is_dark(r, c) and _is_player_piece(_get(board, r, c), player):
                caps = _get_capture_moves(board, player, r, c, ((r, c),))
                captures.extend(caps)
    if captures:
        return captures
    # No captures: simple moves
    simple: list[Move] = []
    for r in range(ROWS):
        for c in range(COLS):
            if _is_dark(r, c) and _is_player_piece(_get(board, r, c), player):
                simple.extend(_get_simple_moves(board, player, r, c))
    return simple


def _apply_move(board: Board, move: Move, player: int) -> Board:
    """Apply a move path to the board."""
    path = list(move)
    if len(path) < 2:
        return board
    r0, c0 = path[0]
    piece = _get(board, r0, c0)
    new_board = _set(board, r0, c0, 0)

    for i in range(1, len(path)):
        r1, c1 = path[i]
        # Remove captured piece if jump
        if abs(r1 - r0) == 2:
            mid_r, mid_c = (r0 + r1) // 2, (c0 + c1) // 2
            new_board = _set(new_board, mid_r, mid_c, 0)
        # Promote to king when reaching back row
        if player == 0 and r1 == ROWS - 1:
            piece = 2
        elif player == 1 and r1 == 0:
            piece = 4
        new_board = _set(new_board, r1, c1, piece)
        r0, c0 = r1, c1
    return new_board


def _count_pieces(board: Board, player: int) -> int:
    if player == 0:
        return sum(1 for c in board if c in (1, 2))
    return sum(1 for c in board if c in (3, 4))


def initial_state() -> State:
    """Initial 6×6 checkers setup: 6 pieces per side on dark squares of first 2 rows."""
    board = [0] * SIZE
    # Player 0 at rows 0,1 (bottom)
    for r in (0, 1):
        for c in range(COLS):
            if _is_dark(r, c):
                board[_idx(r, c)] = 1
    # Player 1 at rows 4,5 (top)
    for r in (4, 5):
        for c in range(COLS):
            if _is_dark(r, c):
                board[_idx(r, c)] = 3
    return (tuple(board), 0)


class Checkers:
    def get_current_player(self, state: State) -> int:
        return state[1]

    def get_legal_actions(self, state: State) -> list[Move]:
        board, player = state
        if self.is_terminal(state):
            return []
        return _get_all_moves(board, player)

    def apply_action(self, state: State, action: Move) -> State:
        board, player = state
        new_board = _apply_move(board, action, player)
        # If was a capture and more captures possible from landing square, same player moves again
        # For simplicity: we only return one move per action; multi-jump is one action.
        # So we always alternate turns.
        next_player = 1 - player
        return (new_board, next_player)

    def is_terminal(self, state: State) -> bool:
        board, player = state
        if _count_pieces(board, 0) == 0 or _count_pieces(board, 1) == 0:
            return True
        if not _get_all_moves(board, player):
            return True
        return False

    def get_outcome(self, state: State) -> dict[int, float]:
        board, player = state
        p0 = _count_pieces(board, 0)
        p1 = _count_pieces(board, 1)
        if p0 == 0:
            return {0: 0.0, 1: 1.0}
        if p1 == 0:
            return {0: 1.0, 1: 0.0}
        # No legal moves = current player loses
        if not _get_all_moves(board, player):
            return {0: 0.0 if player == 0 else 1.0, 1: 1.0 if player == 0 else 0.0}
        return {0: 0.5, 1: 0.5}


def format_board(state: State) -> str:
    board, _ = state
    chars = {0: ".", 1: "o", 2: "O", 3: "x", 4: "X"}
    lines = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            if _is_dark(r, c):
                row.append(chars.get(board[_idx(r, c)], "?"))
            else:
                row.append(" ")
        lines.append(" ".join(row))
    lines.append(" ".join(str(c + 1) for c in range(COLS)))
    return "\n".join(lines)


def move_to_str(move: Move) -> str:
    """Compact string for a move, e.g. 'a1-b2' or 'a1xc3xe5'."""
    def sq(r: int, c: int) -> str:
        col = chr(ord("a") + c)
        row = str(ROWS - r)
        return f"{col}{row}"
    parts = [sq(r, c) for r, c in move]
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}"
    return "x".join(parts)


def parse_move(s: str) -> Move | None:
    """Parse move like 'a6-b5' or 'a6xc4xe2'. Returns None if invalid."""
    s = s.strip().lower().replace(" ", "")
    if "-" in s:
        parts = s.split("-")
    elif "x" in s:
        parts = s.split("x")
    else:
        return None
    if len(parts) < 2:
        return None
    path = []
    for p in parts:
        if len(p) < 2:
            return None
        col = ord(p[0]) - ord("a")
        try:
            row_num = int(p[1])
        except ValueError:
            return None
        row = ROWS - row_num
        if 0 <= row < ROWS and 0 <= col < COLS and _is_dark(row, col):
            path.append((row, col))
        else:
            return None
    return tuple(path)
