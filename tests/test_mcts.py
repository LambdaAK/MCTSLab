"""
Quick test for the MCTS framework.
"""

from __future__ import annotations

from mcts import run_mcts


class MicroGame:
    """Tiny 2-player game: state = (steps_left, last_player). Alternate moves; when steps hit 0, last_player wins."""

    def get_current_player(self, state: tuple[int, int | None]) -> int:
        steps, _ = state
        if steps <= 0:
            return 0
        return (3 - steps) % 2

    def get_legal_actions(self, state: tuple[int, int | None]) -> list[int]:
        if state[0] <= 0:
            return []
        return [0, 1]

    def apply_action(
        self, state: tuple[int, int | None], action: int
    ) -> tuple[int, int | None]:
        steps, _ = state
        current = self.get_current_player(state)
        return (steps - 1, current)

    def is_terminal(self, state: tuple[int, int | None]) -> bool:
        return state[0] <= 0

    def get_outcome(self, state: tuple[int, int | None]) -> dict[int, float]:
        _, last_player = state
        if last_player is None:
            return {0: 0.5, 1: 0.5}
        return {0: 1.0 if last_player == 0 else 0.0, 1: 1.0 if last_player == 1 else 0.0}


def test_run_mcts_returns_root_and_best_action() -> None:
    game = MicroGame()
    state = (3, None)
    root, best_action = run_mcts(game, state, num_simulations=50)
    assert root is not None
    assert best_action in (0, 1)
    assert root.visits >= 50


def test_run_mcts_terminal_state() -> None:
    game = MicroGame()
    state = (0, 1)
    root, best_action = run_mcts(game, state, num_simulations=10)
    assert best_action is None
    assert root.visits == 10
