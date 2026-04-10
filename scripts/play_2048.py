#!/usr/bin/env python3
"""
2048: watch MCTS play (auto-run with optional delay), or play yourself.
Usage:
  python scripts/play_2048.py              # watch (1s delay)
  python scripts/play_2048.py --delay 0  # watch, no delay
  python scripts/play_2048.py --play     # human plays with WASD
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


def best_tile(state) -> int:
    board, _ = state
    return max(board)


def sample_chance(game: Game2048, state, rng: random.Random) -> tuple:
    """Resolve chance node: sample one (new_state, prob) and return new_state."""
    outcomes = game.apply_action(state, None)
    if isinstance(outcomes, list):
        states, probs = zip(*outcomes)
        return rng.choices(states, weights=probs, k=1)[0]
    return outcomes


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
        ui.print_result(f"Game over.  Score: {score(state)}  Moves: {move_num}  Max tile: {best_tile(state)}")
    else:
        print(f"Game over. Score: {score(state)}  Moves: {move_num}  Max tile: {best_tile(state)}")


def play_human(
    *,
    hint_simulations: int = 0,
    seed: int | None = None,
) -> None:
    game = Game2048()
    state = initial_state(seed=seed)
    rng = random.Random(seed)
    hint_rng = random.Random(None if seed is None else seed + 1)
    move_num = 0
    last_move: str | None = None

    key_to_dir = {
        "w": 0,
        "d": 1,
        "s": 2,
        "a": 3,
        "up": 0,
        "right": 1,
        "down": 2,
        "left": 3,
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
    }

    if use_rich:
        ui.print_2048_board(state)
        ui.print_2048_watch_info(move_num, score(state), last_move)
    else:
        print(format_board_2048(state))
        print(f"Move {move_num}  Score: {score(state)}  Last: {last_move or '-'}")
    print("Controls: W/A/S/D (or up/left/down/right). Type q to quit.")

    while not game.is_terminal(state):
        legal = game.get_legal_actions(state)
        legal_names = [direction_name(d) for d in legal]

        if hint_simulations > 0:
            _, hint = run_mcts(game, state, num_simulations=hint_simulations, rng=hint_rng)
            if hint in legal:
                print(f"Hint: {direction_name(hint)}")

        print(f"Your move ({'/'.join(legal_names)}): ", end="")
        try:
            token = input().strip().lower()
        except EOFError:
            print()
            break

        if token in ("q", "quit", "exit"):
            print("Quitting.")
            break
        if token not in key_to_dir:
            print("Invalid input. Use W/A/S/D (or up/right/down/left).")
            continue

        action = key_to_dir[token]
        if action not in legal:
            print(f"Illegal move from this position. Legal: {', '.join(legal_names)}")
            continue

        state = game.apply_action(state, action)  # (board, "chance")
        state = sample_chance(game, state, rng)
        move_num += 1
        last_move = direction_name(action)

        if use_rich:
            ui.console.clear()
            ui.print_2048_board(state)
            ui.print_2048_watch_info(move_num, score(state), last_move)
        else:
            print()
            print(format_board_2048(state))
            print(f"Move {move_num}  Score: {score(state)}  Last: {last_move}")

    if game.is_terminal(state):
        if use_rich:
            ui.print_result(f"Game over.  Score: {score(state)}  Moves: {move_num}  Max tile: {best_tile(state)}")
        else:
            print(f"Game over. Score: {score(state)}  Moves: {move_num}  Max tile: {best_tile(state)}")


def main() -> None:
    p = argparse.ArgumentParser(description="2048: watch MCTS play or play yourself")
    p.add_argument("--simulations", type=int, default=800, help="MCTS simulations per move (2048 is slow; use 500–1000)")
    p.add_argument("--delay", type=float, default=1.0, help="Seconds between moves (0 = no delay)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible game")
    p.add_argument("--play", action="store_true", help="Human plays with WASD input")
    p.add_argument("--hint-simulations", type=int, default=0, help="If >0 in --play mode, show MCTS hint each turn")
    args = p.parse_args()

    if args.play:
        play_human(hint_simulations=args.hint_simulations, seed=args.seed)
        return
    watch(num_simulations=args.simulations, delay=args.delay, seed=args.seed)


if __name__ == "__main__":
    main()
