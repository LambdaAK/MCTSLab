"""
Default rollout policy: play to termination with uniform random choices.

Supports both deterministic and stochastic transitions (chance nodes).
"""

from __future__ import annotations

import random
from typing import Any

from mcts.game import Game


def rollout_until_terminal(
    game: Game,
    state: Any,
    *,
    rng: random.Random | None = None,
) -> dict[Any, float]:
    """
    From the given state, follow a random path to a terminal state and return the outcome.

    - For a player turn: choose uniformly among legal actions; apply the action (deterministic).
    - For a chance node (get_current_player(state) == "chance"): get outcomes from
      apply_action and sample by probability.

    The state is not mutated; the game must return new states from apply_action.
    """
    rng = rng or random.Random()
    while not game.is_terminal(state):
        player = game.get_current_player(state)
        legal = game.get_legal_actions(state)

        if player == "chance":
            # Expect apply_action(state, action) to return list of (state, prob).
            # If legal is empty, we use a single "tick" action for chance.
            if not legal:
                # Some games use get_legal_actions returning [None] for chance
                result = game.apply_action(state, None)
            else:
                result = game.apply_action(state, rng.choice(legal))

            if isinstance(result, list):
                states, probs = zip(*result)
                state = rng.choices(states, weights=probs, k=1)[0]
            else:
                state = result
            continue

        if not legal:
            break
        if hasattr(game, "rollout_action"):
            action = game.rollout_action(state, legal, rng)
        else:
            action = rng.choice(legal)
        result = game.apply_action(state, action)

        if isinstance(result, list):
            states, probs = zip(*result)
            state = rng.choices(states, weights=probs, k=1)[0]
        else:
            state = result

    return game.get_outcome(state)
