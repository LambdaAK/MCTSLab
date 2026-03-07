"""
Flat UCB: UCB1 over root actions only — no tree expansion below the root.

Each iteration we pick a root action (by UCB1 or expand if unexpanded), rollout from
the resulting state, and update that action's statistics. No grandchildren.
Useful as a baseline to compare against full UCT.
"""

from __future__ import annotations

import math
import random
from typing import Any, Optional

from mcts.game import Game
from mcts.node import Node
from mcts.rollout import rollout_until_terminal


def _sample_successor(game: Game, state: Any, action: Any, rng: random.Random) -> Any:
    result = game.apply_action(state, action)
    if isinstance(result, list):
        states, probs = zip(*result)
        return rng.choices(states, weights=probs, k=1)[0]
    return result


def _select_child_ucb(root: Node, exploration: float) -> Optional[Node]:
    """Select root child by UCB1; prefer unvisited."""
    if not root.children:
        return None
    best: Optional[Node] = None
    best_value = -float("inf")
    for child in root.children.values():
        if child.visits == 0:
            return child
        ucb = (child.total_reward / child.visits) + exploration * (
            math.log(root.visits + 1) / child.visits
        ) ** 0.5
        if ucb > best_value:
            best_value = ucb
            best = child
    return best


def run_flat_ucb(
    game: Game,
    state: Any,
    *,
    num_simulations: int = 1000,
    exploration: float = 1.414,
    rng: Optional[random.Random] = None,
) -> tuple[Node, Optional[Any]]:
    """
    Run Flat UCB from the given state: UCB1 over root actions only, no tree below.

    Returns (root, best_action). Root has one child per legal action; we never
    expand beyond that. Best action = most visited child.
    """
    rng = rng or random.Random()
    root = Node(
        state,
        parent=None,
        action=None,
        current_player=game.get_current_player(state),
    )
    root_player = root.current_player

    for _ in range(num_simulations):
        if game.is_terminal(root.state):
            break

        legal = game.get_legal_actions(root.state)
        if not legal:
            break

        unexpanded = [a for a in legal if a not in root.children]
        if unexpanded:
            action = rng.choice(unexpanded)
            new_state = _sample_successor(game, root.state, action, rng)
            child = Node(
                new_state,
                parent=root,
                action=action,
                current_player=game.get_current_player(new_state),
            )
            root.children[action] = child
            node_to_rollout = child
        else:
            child = _select_child_ucb(root, exploration)
            if child is None:
                break
            node_to_rollout = child

        outcome = rollout_until_terminal(game, node_to_rollout.state, rng=rng)
        # Backprop only to node_to_rollout and root
        reward_child = outcome.get(root.current_player, 0.0)
        reward_root = outcome.get(root_player, 0.0)
        node_to_rollout.visits += 1
        node_to_rollout.total_reward += reward_child
        root.visits += 1
        root.total_reward += reward_root

    best_child = root.most_visited_child()
    if best_child is None:
        return root, None
    return root, best_child.action
