#!/usr/bin/env python3
"""
2048: watch MCTS play (auto-run with optional delay), or play yourself.
Usage:
  python scripts/play_2048.py              # watch (1s delay)
  python scripts/play_2048.py --delay 0  # watch, no delay
  python scripts/play_2048.py --play     # human plays (future)
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcts import run_mcts

from games.game_2048 import Game2048, initial_state, direction_name, format_board_2048

try:
    import ui
    use_rich = ui.is_rich_available()
except ImportError:
    use_rich = False


def score(state) -> int:
    board, _ = state
    return sum(board)


def sample_chance(game: Game2048, state, rng: random.Random) -> tuple:
    """Resolve chance node: sample one (new_state, prob) and return new_state."""
    outcomes = game.apply_action(state, None)
    states, probs = zip(*outcomes)
    return rng.choices(states, weights=probs, k=1)[0]


def watch(
    num_simulations: int = 1500,
    delay: float = 1.0,
    seed: int | None = None,
) -> None:
    game = Game2048()
    state = initial_state(seed=seed)
    rng = random.Random(seed)
    move_num = 0
    last_move: str | None = None

    if use_rich:
        ui.print_2048_board(state)
        ui.print_2048_watch_info(0, score(state), None)
        console = ui.console
    else:
        print(format_board_2048(state))
        print(f"Score: {score(state)}\n")

    while not game.is_terminal(state):
        # MCTS chooses direction (player turn)
        if use_rich:
            ui.console.print("[dim]Thinking…[/]")
        else:
            print("Thinking…")
        _, action = run_mcts(game, state, num_simulations=num_simulations, rng=rng)
        if action is None:
            break
        state = game.apply_action(state, action)  # -> (board, "chance")
        # Resolve chance: spawn one tile
        state = sample_chance(game, state, rng)
        move_num += 1
        last_move = direction_name(action)
        s = score(state)

        if use_rich:
            console.clear()
            ui.print_2048_board(state)
            ui.print_2048_watch_info(move_num, s, last_move)
        else:
            print(format_board_2048(state))
            print(f"Move {move_num}  Score: {s}  Last: {last_move}\n")

        if delay > 0:
            time.sleep(delay)

    # Final
    if use_rich:
        ui.print_result(f"Game over.  Score: {score(state)}  Moves: {move_num}")
    else:
        print(f"Game over. Score: {score(state)}  Moves: {move_num}")


def main() -> None:
    p = argparse.ArgumentParser(description="2048: watch MCTS play or play yourself")
    p.add_argument("--simulations", type=int, default=800, help="MCTS simulations per move (2048 is slow; use 500–1000)")
    p.add_argument("--delay", type=float, default=1.0, help="Seconds between moves (0 = no delay)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible game")
    p.add_argument("--play", action="store_true", help="Human plays (not implemented yet)")
    args = p.parse_args()

    if args.play:
        print("Human play not implemented yet. Use watch mode (default).")
        return
    watch(num_simulations=args.simulations, delay=args.delay, seed=args.seed)


if __name__ == "__main__":
    main()
