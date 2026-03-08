"""
Dots and Boxes: grid of dots, players claim edges. Completing a box scores 1 point and grants another turn.
State = (edges, current_player, score0, score1). Edges: 0=unclaimed, 1=player 0, 2=player 1.
Actions are edge indices 0..num_edges-1.
"""

from __future__ import annotations

from typing import Any

from mcts.game import Game

# Grid: R rows × C columns of boxes (so (R+1)×(C+1) dots)
ROWS = 4
COLS = 4

# Edge counts: horizontal = (R+1)*C, vertical = (C+1)*R
NUM_H_EDGES = (ROWS + 1) * COLS
NUM_V_EDGES = (COLS + 1) * ROWS
NUM_EDGES = NUM_H_EDGES + NUM_V_EDGES

# State: (edges_tuple, current_player, score0, score1, box_owners)
# box_owners: tuple of ROWS*COLS, 0=unclaimed, 1=player0, 2=player1 (set when box completed)
State = tuple[tuple[int, ...], int, int, int, tuple[int, ...]]


def _box_edges(r: int, c: int) -> tuple[int, int, int, int]:
    """Return (top, bottom, left, right) edge indices for box (r, c)."""
    top = r * COLS + c
    bottom = (r + 1) * COLS + c
    left = NUM_H_EDGES + r * (COLS + 1) + c
    right = NUM_H_EDGES + r * (COLS + 1) + c + 1
    return (top, bottom, left, right)


def _boxes_for_edge(edge_idx: int) -> list[tuple[int, int]]:
    """Return list of (r, c) box indices that include this edge."""
    boxes: list[tuple[int, int]] = []
    if edge_idx < NUM_H_EDGES:
        # Horizontal edge: row r, between cols c and c+1
        r = edge_idx // COLS
        c = edge_idx % COLS
        if r > 0:
            boxes.append((r - 1, c))  # box above
        if r < ROWS:
            boxes.append((r, c))  # box below
    else:
        # Vertical edge
        v_idx = edge_idx - NUM_H_EDGES
        r = v_idx // (COLS + 1)
        c = v_idx % (COLS + 1)
        if c > 0:
            boxes.append((r, c - 1))  # box to the left
        if c < COLS:
            boxes.append((r, c))  # box to the right
    return boxes


def _is_box_complete(edges: tuple[int, ...], box: tuple[int, int]) -> bool:
    """True if all 4 edges of the box are claimed."""
    te, be, le, re = _box_edges(box[0], box[1])
    return all(edges[e] != 0 for e in (te, be, le, re))


def initial_state() -> State:
    edges = (0,) * NUM_EDGES
    box_owners = (0,) * (ROWS * COLS)
    return (edges, 0, 0, 0, box_owners)


class DotsAndBoxes:
    def get_current_player(self, state: State) -> int:
        return state[1]

    def get_legal_actions(self, state: State) -> list[int]:
        edges, _, _, _, _ = state
        if self.is_terminal(state):
            return []
        return [i for i in range(NUM_EDGES) if edges[i] == 0]

    def apply_action(self, state: State, action: int) -> State:
        edges, current, score0, score1, box_owners = state
        player_val = current + 1  # 1 or 2

        # Claim the edge
        new_edges = list(edges)
        new_edges[action] = player_val
        new_edges = tuple(new_edges)

        # Check which boxes were completed by this move (current player gets them)
        boxes = _boxes_for_edge(action)
        new_box_owners = list(box_owners)
        new_boxes = 0
        for (r, c) in boxes:
            if _is_box_complete(new_edges, (r, c)):
                new_box_owners[r * COLS + c] = player_val
                new_boxes += 1
        new_box_owners = tuple(new_box_owners)

        if current == 0:
            new_score0 = score0 + new_boxes
            new_score1 = score1
        else:
            new_score0 = score0
            new_score1 = score1 + new_boxes

        # If player completed at least one box, they get another turn
        next_player = current if new_boxes > 0 else (1 - current)

        return (new_edges, next_player, new_score0, new_score1, new_box_owners)

    def is_terminal(self, state: State) -> bool:
        edges, _, _, _, _ = state
        return all(e != 0 for e in edges)

    def get_outcome(self, state: State) -> dict[int, float]:
        _, _, score0, score1, _ = state
        if score0 > score1:
            return {0: 1.0, 1: 0.0}
        if score1 > score0:
            return {0: 0.0, 1: 1.0}
        return {0: 0.5, 1: 0.5}


def _box_owner_from_state(state: State, r: int, c: int) -> int | None:
    """Return 1 or 2 if box (r,c) is complete and owned, else None. Uses recorded ownership."""
    edges, _, _, _, box_owners = state
    if not _is_box_complete(edges, (r, c)):
        return None
    owner = box_owners[r * COLS + c]
    return owner if owner else None


def format_board(state: State) -> str:
    """ASCII representation with 1-based edge numbers and box ownership."""
    edges, current, score0, score1, _ = state
    lines: list[str] = []

    def h_label(idx: int) -> str:
        n = idx + 1
        if edges[idx] == 0:
            return f" {n:2} "
        return " X  " if edges[idx] == 1 else " O  "

    def v_label(idx: int) -> str:
        n = idx + 1
        if edges[idx] == 0:
            return f"{n:2}"
        return "X " if edges[idx] == 1 else "O "

    def box_center(r: int, c: int) -> str:
        owner = _box_owner_from_state(state, r, c)
        return "X" if owner == 1 else "O" if owner == 2 else " "

    for dr in range(ROWS + 1):
        row_str = "●"
        for dc in range(COLS):
            idx = dr * COLS + dc
            row_str += "───" + h_label(idx) + "───●"
        lines.append(row_str)

        if dr < ROWS:
            v_row = ""
            for dc in range(COLS + 1):
                idx = NUM_H_EDGES + dr * (COLS + 1) + dc
                v_row += v_label(idx) + "│"
                if dc < COLS:
                    v_row += box_center(dr, dc) + "│"
            lines.append(v_row)

    lines.append("")
    lines.append(f"Scores: You={score0}  Bot={score1}  |  Current: {'You' if current == 0 else 'Bot'}")
    lines.append(f"Enter 1–{NUM_EDGES} to claim. 1–{NUM_H_EDGES}=horizontal, {NUM_H_EDGES+1}–{NUM_EDGES}=vertical.")
    return "\n".join(lines)
