#!/usr/bin/env python3
"""
Benchmark MCTS (UCT or Flat UCB) vs random player. Report win/draw/loss rate
for different parameter settings.
"""

from __future__ import annotations

import argparse
import random
import sys
from typing import Any, Callable

import os
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from mcts import run_mcts, run_flat_ucb


def play_one_game(
    game: Any,
    initial_state: Any,
    player0_choose: Callable[[Any, Any], Any],
    player1_choose: Callable[[Any, Any], Any],
    rng: random.Random,
) -> float:
    """
    Play one game. player0_choose(game, state) returns action for state (player 0 to move).
    Returns outcome for player 0: 1.0 = win, 0.0 = loss, 0.5 = draw.
    """
    state = initial_state
    while not game.is_terminal(state):
        current = game.get_current_player(state)
        legal = game.get_legal_actions(state)
        if not legal:
            break
        if current == 0:
            action = player0_choose(game, state)
        else:
            action = player1_choose(game, state)
        if action is None or action not in legal:
            action = rng.choice(legal)
        result = game.apply_action(state, action)
        state = result if not isinstance(result, list) else rng.choices([s for s, _ in result], weights=[p for _, p in result], k=1)[0]
    outcome = game.get_outcome(state)
    return outcome.get(0, 0.5)


def random_player(game: Any, state: Any, rng: random.Random) -> Any:
    legal = game.get_legal_actions(state)
    if not legal:
        return None
    return rng.choice(legal)


def mcts_player(
    game: Any,
    state: Any,
    run_bot: Callable,
    num_simulations: int,
    exploration: float,
    rng: random.Random,
) -> Any:
    root, action = run_bot(game, state, num_simulations=num_simulations, exploration=exploration, rng=rng)
    return action


def run_benchmark(
    game_name: str,
    variant: str,
    num_simulations: int,
    exploration: float,
    games_per_side: int,
    seed: int | None,
) -> tuple[float, float, float]:
    """
    Run 2*games_per_side games: games_per_side with MCTS as player 0, games_per_side with MCTS as player 1.
    Returns (win_rate, draw_rate, loss_rate) for MCTS.
    """
    if game_name == "tictactoe":
        from games.tictactoe import TicTacToe, initial_state
        game = TicTacToe()
    elif game_name == "connect4":
        from games.connect_four import ConnectFour, initial_state
        game = ConnectFour()
    else:
        from games.checkers import Checkers, initial_state
        game = Checkers()

    run_bot = run_flat_ucb if variant == "flat_ucb" else run_mcts
    rng = random.Random(seed)

    wins = 0
    draws = 0
    losses = 0

    def mcts_p0(g, s):
        return mcts_player(g, s, run_bot, num_simulations, exploration, rng)

    def mcts_p1(g, s):
        return mcts_player(g, s, run_bot, num_simulations, exploration, rng)

    def rand_p(g, s):
        return random_player(g, s, rng)

    n = games_per_side
    for _ in range(n):
        outcome = play_one_game(game, initial_state(), mcts_p0, rand_p, rng)
        if outcome >= 0.99:
            wins += 1
        elif outcome <= 0.01:
            losses += 1
        else:
            draws += 1
    for _ in range(n):
        outcome = play_one_game(game, initial_state(), rand_p, mcts_p1, rng)
        if outcome <= 0.01:
            wins += 1
        elif outcome >= 0.99:
            losses += 1
        else:
            draws += 1

    total = 2 * n
    return wins / total, draws / total, losses / total


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark MCTS vs random player")
    p.add_argument("--game", choices=["tictactoe", "connect4", "checkers"], default="tictactoe")
    p.add_argument("--variant", choices=["uct", "flat_ucb"], default="uct")
    p.add_argument("--games", type=int, default=50, help="Games per side (total = 2*games)")
    p.add_argument("--simulations", type=int, nargs="+", default=[100, 500, 1000], help="Simulation counts to compare (e.g. 100 500 1000)")
    p.add_argument("--exploration", type=float, default=1.414, help="UCB exploration constant")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = p.parse_args()

    print(f"Benchmark: MCTS ({args.variant}) vs random — {args.game}")
    print(f"  {2 * args.games} games total ({args.games} with MCTS first, {args.games} with random first)")
    print(f"  exploration = {args.exploration}")
    print()
    print(f"{'Simulations':>12}  {'Win%':>8}  {'Draw%':>8}  {'Loss%':>8}")
    print("-" * 44)

    for sims in args.simulations:
        win, draw, loss = run_benchmark(
            args.game,
            args.variant,
            num_simulations=sims,
            exploration=args.exploration,
            games_per_side=args.games,
            seed=args.seed,
        )
        print(f"{sims:>12}  {win*100:>7.1f}%  {draw*100:>7.1f}%  {loss*100:>7.1f}%")


if __name__ == "__main__":
    main()
