"""
UCT (Upper Confidence Bound applied to Trees) implementation.

One iteration = select until expandable or terminal -> expand one node -> rollout -> backprop.
Supports deterministic and stochastic (chance) transitions.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from mcts.game import Game
from mcts.node import Node
from mcts.rollout import rollout_until_terminal


def _is_chance(game: Game, state: Any) -> bool:
    return game.get_current_player(state) == "chance"


def _sample_successor(game: Game, state: Any, action: Any, rng: random.Random) -> Any:
    """Return a single successor state; if stochastic, sample by probability."""
    result = game.apply_action(state, action)
    if isinstance(result, list):
        states, probs = zip(*result)
        return rng.choices(states, weights=probs, k=1)[0]
    return result


def _sample_chance_outcome(game: Game, state: Any, rng: random.Random) -> Any:
    """Get legal 'actions' for chance (e.g. [None]), then sample one outcome."""
    legal = game.get_legal_actions(state)
    if not legal:
        result = game.apply_action(state, None)
    else:
        result = game.apply_action(state, rng.choice(legal))

    if isinstance(result, list):
        states, probs = zip(*result)
        return rng.choices(states, weights=probs, k=1)[0]
    return result


def _backprop(node: Node, outcome: dict[Any, float], root_player: Any) -> None:
    """Update visits and total_reward along the path from node to root."""
    current: Optional[Node] = node
    while current is not None:
        current.visits += 1
        # Reward for the player who moved to this node (parent's current player, or root player for root)
        if current.parent is not None:
            reward = outcome.get(current.parent.current_player, 0.0)
        else:
            reward = outcome.get(root_player, 0.0)
        current.total_reward += reward
        current = current.parent


def one_uct_iteration(
    game: Game,
    root: Node,
    *,
    exploration: float = 1.414,
    rng: Optional[random.Random] = None,
) -> None:
    """
    Run one MCTS iteration: select, expand, rollout, backprop.

    Modifies the tree rooted at `root` in place.
    """
    rng = rng or random.Random()
    node = root
    root_player = root.current_player

    # Selection
    while True:
        if game.is_terminal(node.state):
            outcome = game.get_outcome(node.state)
            _backprop(node, outcome, root_player)
            return

        current_player = game.get_current_player(node.state)

        if current_player == "chance":
            if not node.children:
                # Expand: sample one chance outcome, create child, rollout from child
                new_state = _sample_chance_outcome(game, node.state, rng)
                child = Node(
                    new_state,
                    parent=node,
                    action=None,
                    current_player=game.get_current_player(new_state),
                )
                key = len(node.children)  # key for chance children
                node.children[key] = child
                outcome = rollout_until_terminal(game, new_state, rng=rng)
                _backprop(child, outcome, root_player)
                return
            # Select among chance children at random (could use visit-based later)
            key = rng.choice(list(node.children))
            node = node.children[key]
            continue

        legal = game.get_legal_actions(node.state)
        if not legal:
            outcome = game.get_outcome(node.state) if game.is_terminal(node.state) else {}
            _backprop(node, outcome, root_player)
            return

        unexpanded = [a for a in legal if a not in node.children]
        if unexpanded:
            # Expand one action (and possibly sample if stochastic)
            action = rng.choice(unexpanded)
            new_state = _sample_successor(game, node.state, action, rng)
            child = Node(
                new_state,
                parent=node,
                action=action,
                current_player=game.get_current_player(new_state),
            )
            node.children[action] = child
            outcome = rollout_until_terminal(game, new_state, rng=rng)
            _backprop(child, outcome, root_player)
            return

        # Fully expanded: select by UCB
        next_node = node.best_child(exploration=exploration)
        if next_node is None:
            return
        node = next_node


def run_mcts(
    game: Game,
    state: Any,
    *,
    num_simulations: int = 1000,
    exploration: float = 1.414,
    rng: Optional[random.Random] = None,
) -> tuple[Node, Optional[Any]]:
    """
    Build an MCTS tree from the given state and return (root, best_action).

    best_action is the action leading to the most-visited child (None if no legal actions or no simulations).
    """
    rng = rng or random.Random()
    root = Node(
        state,
        parent=None,
        action=None,
        current_player=game.get_current_player(state),
    )

    for _ in range(num_simulations):
        one_uct_iteration(game, root, exploration=exploration, rng=rng)

    best_child = root.most_visited_child()
    if best_child is None:
        return root, None
    return root, best_child.action
