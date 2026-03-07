"""
MCTS tree node.

Each node stores a game state, the move that led to it, and statistics
(visits, total reward) for UCT selection and backpropagation.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from mcts.game import PlayerId


class Node:
    """
    A node in the MCTS tree.

    - state: the game state at this node (immutable / not mutated by MCTS).
    - parent: the node we came from (None for root).
    - action: the action that led from parent to this node (None for root).
    - current_player: who is to move in state (used for backprop reward attribution).
    - children: map action -> Node for expanded successors.
    - visits: number of times this node was on the backprop path.
    - total_reward: sum of rewards (for the player who moved to this node) from backprops.
    """

    __slots__ = (
        "state",
        "parent",
        "action",
        "current_player",
        "children",
        "visits",
        "total_reward",
    )

    def __init__(
        self,
        state: Any,
        *,
        parent: Optional[Node] = None,
        action: Any = None,
        current_player: PlayerId = 0,
    ) -> None:
        self.state = state
        self.parent = parent
        self.action = action
        self.current_player = current_player
        self.children: dict[Any, Node] = {}
        self.visits: int = 0
        self.total_reward: float = 0.0

    def is_root(self) -> bool:
        return self.parent is None

    def is_fully_expanded(self, legal_actions: list[Any]) -> bool:
        """True if every legal action has a child node."""
        return all(a in self.children for a in legal_actions)

    def best_child(self, exploration: float = 1.414) -> Optional[Node]:
        """
        Return the child that maximizes UCB1.

        exploration: sqrt(2) is a common default. Only used when all children have visits > 0.
        """
        if not self.children:
            return None
        best: Optional[Node] = None
        best_value = -float("inf")
        for child in self.children.values():
            if child.visits == 0:
                return child  # prefer unvisited
            ucb = (child.total_reward / child.visits) + exploration * (
                math.log(self.visits + 1) / child.visits
            ) ** 0.5
            if ucb > best_value:
                best_value = ucb
                best = child
        return best

    def most_visited_child(self) -> Optional[Node]:
        """Return the child with the most visits (typical choice for best move)."""
        if not self.children:
            return None
        return max(self.children.values(), key=lambda n: n.visits)
