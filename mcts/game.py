"""
Game interface for MCTS.

Any game used by the MCTS framework must provide these operations on states.
States should be immutable or treated as copy-on-write; the framework never mutates them.
"""

from __future__ import annotations

from typing import Any, Protocol, Union

# Player who is to move: an int (e.g. 0, 1) or "chance" for stochastic transitions.
PlayerId = Union[int, str]

# Outcome when state is terminal: reward per player (e.g. {0: 1.0, 1: 0.0} for player 0 wins).
Outcome = dict[Union[int, str], float]

# Deterministic: apply_action returns a single new state.
# Stochastic: apply_action returns a list of (state, probability) pairs.
ApplyResult = Union[Any, list[tuple[Any, float]]]


class Game(Protocol):
    """
    Protocol that any game must implement for use with MCTS.

    The game object is stateless; all methods take a state argument.
    """

    def get_current_player(self, state: Any) -> PlayerId:
        """Return the player who is to move in this state, or 'chance' for stochastic transitions."""
        pass

    def get_legal_actions(self, state: Any) -> list[Any]:
        """Return the list of legal actions in this state. Empty if terminal or at a chance node."""
        pass

    def apply_action(self, state: Any, action: Any) -> ApplyResult:
        """
        Apply the action to the state and return the result.

        - Deterministic: return the new state (single object).
        - Stochastic: return a list of (new_state, probability) pairs.
        """
        pass

    def is_terminal(self, state: Any) -> bool:
        """Return True if the state is terminal (game over)."""
        pass

    def get_outcome(self, state: Any) -> Outcome:
        """
        Return the outcome for each player. Only valid when is_terminal(state) is True.

        Typical convention: 1.0 = win, 0.0 = loss, 0.5 = draw for that player.
        """
        pass
