#!/usr/bin/env python3
"""
Round-robin arena for MCTSLab bots.

Examples:
  python scripts/arena.py --game connect4
  python scripts/arena.py --game checkers --bots uct:1500 flat_ucb:1500 random
  python scripts/arena.py --game tictactoe --bots "strong=uct:4000" "fast=uct:800" random
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import os
import random
import sys
from typing import Any, Callable

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from mcts import run_flat_ucb, run_mcts


@dataclass(frozen=True)
class BotSpec:
    name: str
    variant: str  # "uct" | "flat_ucb" | "random"
    simulations: int


@dataclass
class BotStanding:
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: float = 0.0
    elo: float = 1500.0


@dataclass(frozen=True)
class PairResult:
    bot_a: str
    bot_b: str
    games: int
    wins_a: int
    draws: int
    wins_b: int
    score_a: float  # average points per game for bot_a
    score_b: float


def parse_bot_spec(spec: str) -> BotSpec:
    """
    Parse one bot spec:
      random
      uct:1500
      flat_ucb:3000
      custom_name=uct:2500
    """
    raw = spec.strip()
    if not raw:
        raise ValueError("empty bot spec")

    custom_name = None
    body = raw
    if "=" in raw:
        custom_name, body = raw.split("=", 1)
        custom_name = custom_name.strip()
        body = body.strip()
        if not custom_name:
            raise ValueError(f"invalid bot spec '{spec}': missing custom name")

    if body.lower() == "random":
        return BotSpec(
            name=custom_name or "random",
            variant="random",
            simulations=0,
        )

    if ":" not in body:
        raise ValueError(
            f"invalid bot spec '{spec}'. Expected 'uct:1500', 'flat_ucb:1500', or 'random'"
        )
    variant, sims_s = body.split(":", 1)
    variant = variant.strip().lower()
    if variant == "flat":
        variant = "flat_ucb"
    if variant not in ("uct", "flat_ucb"):
        raise ValueError(f"invalid bot variant '{variant}' in '{spec}'")
    try:
        sims = int(sims_s)
    except ValueError as exc:
        raise ValueError(f"invalid simulation count in '{spec}'") from exc
    if sims <= 0:
        raise ValueError(f"simulations must be positive in '{spec}'")

    default_name = f"{variant}-{sims}"
    return BotSpec(
        name=custom_name or default_name,
        variant=variant,
        simulations=sims,
    )


def _load_game(game_name: str) -> tuple[Any, Callable[[], Any]]:
    if game_name == "tictactoe":
        from games.tictactoe import TicTacToe, initial_state

        return TicTacToe(), initial_state
    if game_name == "connect4":
        from games.connect_four import ConnectFour, initial_state

        return ConnectFour(), initial_state
    if game_name == "checkers":
        from games.checkers import Checkers, initial_state

        return Checkers(), initial_state
    if game_name == "dots":
        from games.dots_and_boxes import DotsAndBoxes, initial_state

        return DotsAndBoxes(), initial_state
    raise ValueError(f"unknown game: {game_name}")


def _sample_result(result: Any, rng: random.Random) -> Any:
    if isinstance(result, list):
        states, probs = zip(*result)
        return rng.choices(states, weights=probs, k=1)[0]
    return result


def _choose_action(
    bot: BotSpec,
    game: Any,
    state: Any,
    legal: list[Any],
    *,
    exploration: float,
    rng: random.Random,
) -> Any:
    if not legal:
        return None
    if bot.variant == "random":
        return rng.choice(legal)

    run_bot = run_flat_ucb if bot.variant == "flat_ucb" else run_mcts
    _, action = run_bot(
        game,
        state,
        num_simulations=bot.simulations,
        exploration=exploration,
        rng=rng,
    )
    if action in legal:
        return action
    return rng.choice(legal)


def _play_one_game(
    game: Any,
    initial_state_fn: Callable[[], Any],
    bot_p0: BotSpec,
    bot_p1: BotSpec,
    *,
    exploration: float,
    rng: random.Random,
) -> float:
    """
    Returns score for player 0 in [0, 1].
    """
    state = initial_state_fn()
    while not game.is_terminal(state):
        legal = game.get_legal_actions(state)
        if not legal:
            break
        current = game.get_current_player(state)
        actor = bot_p0 if current == 0 else bot_p1
        action = _choose_action(
            actor,
            game,
            state,
            legal,
            exploration=exploration,
            rng=rng,
        )
        if action not in legal:
            action = rng.choice(legal)
        state = _sample_result(game.apply_action(state, action), rng)

    outcome = game.get_outcome(state)
    return float(outcome.get(0, 0.5))


def _elo_expected(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))


def _update_elo(a: BotStanding, b: BotStanding, score_a: float, k: float) -> None:
    exp_a = _elo_expected(a.elo, b.elo)
    exp_b = 1.0 - exp_a
    score_b = 1.0 - score_a
    a.elo += k * (score_a - exp_a)
    b.elo += k * (score_b - exp_b)


def _record_result(standing: BotStanding, score: float) -> None:
    standing.games += 1
    if score >= 0.999:
        standing.wins += 1
        standing.points += 1.0
    elif score <= 0.001:
        standing.losses += 1
    else:
        standing.draws += 1
        standing.points += 0.5


def run_arena(
    game_name: str,
    bots: list[BotSpec],
    *,
    games_per_side: int,
    exploration: float,
    seed: int | None,
    elo_k: float,
    show_matchups: bool,
) -> tuple[dict[str, BotStanding], list[PairResult]]:
    game, initial_state_fn = _load_game(game_name)
    rng = random.Random(seed)
    standings = {bot.name: BotStanding() for bot in bots}
    pairs: list[PairResult] = []

    for bot_a, bot_b in itertools.combinations(bots, 2):
        a_w = 0
        b_w = 0
        d = 0

        for _ in range(games_per_side):
            score_p0 = _play_one_game(
                game,
                initial_state_fn,
                bot_a,
                bot_b,
                exploration=exploration,
                rng=rng,
            )
            _record_result(standings[bot_a.name], score_p0)
            _record_result(standings[bot_b.name], 1.0 - score_p0)
            _update_elo(standings[bot_a.name], standings[bot_b.name], score_p0, elo_k)
            if score_p0 >= 0.999:
                a_w += 1
            elif score_p0 <= 0.001:
                b_w += 1
            else:
                d += 1

        for _ in range(games_per_side):
            score_p0 = _play_one_game(
                game,
                initial_state_fn,
                bot_b,
                bot_a,
                exploration=exploration,
                rng=rng,
            )
            score_a = 1.0 - score_p0
            _record_result(standings[bot_a.name], score_a)
            _record_result(standings[bot_b.name], score_p0)
            _update_elo(standings[bot_a.name], standings[bot_b.name], score_a, elo_k)
            if score_a >= 0.999:
                a_w += 1
            elif score_a <= 0.001:
                b_w += 1
            else:
                d += 1

        if show_matchups:
            print(f"{bot_a.name} vs {bot_b.name}: {a_w}-{d}-{b_w} (W-D-L for {bot_a.name})")

        total = 2 * games_per_side
        score_a_total = float(a_w) + 0.5 * float(d)
        pairs.append(
            PairResult(
                bot_a=bot_a.name,
                bot_b=bot_b.name,
                games=total,
                wins_a=a_w,
                draws=d,
                wins_b=b_w,
                score_a=score_a_total / total,
                score_b=(float(total) - score_a_total) / total,
            )
        )

    return standings, pairs


def _print_standings(standings: dict[str, BotStanding]) -> None:
    rows = sorted(
        standings.items(),
        key=lambda kv: (kv[1].elo, kv[1].points, kv[1].wins),
        reverse=True,
    )
    headers = ["Bot", "Elo", "Games", "W", "D", "L", "Points", "Win%"]
    body: list[list[str]] = []
    for name, s in rows:
        win_rate = (100.0 * s.wins / s.games) if s.games else 0.0
        body.append(
            [
                name,
                f"{s.elo:.1f}",
                str(s.games),
                str(s.wins),
                str(s.draws),
                str(s.losses),
                f"{s.points:.1f}",
                f"{win_rate:.1f}%",
            ]
        )

    widths = [len(h) for h in headers]
    for row in body:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))

    def fmt(row: list[str]) -> str:
        return (
            f"{row[0]:<{widths[0]}}  "
            f"{row[1]:>{widths[1]}}  "
            f"{row[2]:>{widths[2]}}  "
            f"{row[3]:>{widths[3]}}  "
            f"{row[4]:>{widths[4]}}  "
            f"{row[5]:>{widths[5]}}  "
            f"{row[6]:>{widths[6]}}  "
            f"{row[7]:>{widths[7]}}"
        )

    print()
    print(fmt(headers))
    print(
        f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}  {'-' * widths[3]}  "
        f"{'-' * widths[4]}  {'-' * widths[5]}  {'-' * widths[6]}  {'-' * widths[7]}"
    )
    for row in body:
        print(fmt(row))


def _print_pairwise_matrix(bots: list[BotSpec], pairs: list[PairResult]) -> None:
    """
    Matrix values are average points per game for row bot vs column bot.
    100% = row always wins, 50% = drawish parity, 0% = row always loses.
    """
    lookup = {(pair.bot_a, pair.bot_b): pair for pair in pairs}
    names = [bot.name for bot in bots]

    col_w = max(8, max(len(name) for name in names))
    headers = ["Bot"] + names

    def fmt(row: list[str]) -> str:
        return f"{row[0]:<{col_w}}  " + "  ".join(f"{cell:>{col_w}}" for cell in row[1:])

    print()
    print("Pairwise Score Matrix (avg points/game):")
    print(fmt(headers))
    print(f"{'-' * col_w}  " + "  ".join("-" * col_w for _ in names))

    for row_bot in names:
        row = [row_bot]
        for col_bot in names:
            if row_bot == col_bot:
                row.append("—")
                continue
            pair = lookup.get((row_bot, col_bot))
            if pair is not None:
                pct = 100.0 * pair.score_a
            else:
                rev = lookup[(col_bot, row_bot)]
                pct = 100.0 * rev.score_b
            row.append(f"{pct:5.1f}%")
        print(fmt(row))


def _export_json(
    path: str,
    *,
    game_name: str,
    bots: list[BotSpec],
    standings: dict[str, BotStanding],
    pairs: list[PairResult],
) -> None:
    rows = sorted(
        standings.items(),
        key=lambda kv: (kv[1].elo, kv[1].points, kv[1].wins),
        reverse=True,
    )
    payload = {
        "game": game_name,
        "bots": [
            {
                "name": bot.name,
                "variant": bot.variant,
                "simulations": bot.simulations,
            }
            for bot in bots
        ],
        "standings": [
            {
                "name": name,
                "games": s.games,
                "wins": s.wins,
                "draws": s.draws,
                "losses": s.losses,
                "points": s.points,
                "elo": s.elo,
            }
            for name, s in rows
        ],
        "pairwise": [
            {
                "bot_a": pair.bot_a,
                "bot_b": pair.bot_b,
                "games": pair.games,
                "wins_a": pair.wins_a,
                "draws": pair.draws,
                "wins_b": pair.wins_b,
                "score_a": pair.score_a,
                "score_b": pair.score_b,
            }
            for pair in pairs
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nExported arena results to {path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Run a bot arena (round-robin tournament)")
    p.add_argument("--game", choices=["tictactoe", "connect4", "checkers", "dots"], default="tictactoe")
    p.add_argument(
        "--bots",
        nargs="+",
        default=["uct:800", "uct:2500", "flat_ucb:2500", "random"],
        help="Bot specs. Examples: uct:1500 flat_ucb:1500 random strong=uct:4000",
    )
    p.add_argument("--games-per-side", type=int, default=12, help="Games with each seating order per matchup")
    p.add_argument("--exploration", type=float, default=1.414)
    p.add_argument("--elo-k", type=float, default=24.0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--quiet-matchups", action="store_true", help="Hide per-matchup W-D-L lines")
    p.add_argument("--no-matrix", action="store_true", help="Skip pairwise score matrix output")
    p.add_argument("--export-json", type=str, default=None, help="Write standings and pairwise data to a JSON file")
    args = p.parse_args()

    bots = [parse_bot_spec(spec) for spec in args.bots]
    names = [b.name for b in bots]
    if len(bots) < 2:
        raise ValueError("need at least two bots for an arena")
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate bot names detected: {names}")

    total_games = len(bots) * (len(bots) - 1) * args.games_per_side
    print(f"Arena: {args.game}")
    print(f"Bots: {', '.join(names)}")
    print(
        "Games: "
        f"{total_games} total "
        f"({args.games_per_side} per side per pair)"
    )
    print(f"Exploration: {args.exploration} | Elo K: {args.elo_k}")
    print()

    standings, pairs = run_arena(
        args.game,
        bots,
        games_per_side=args.games_per_side,
        exploration=args.exploration,
        seed=args.seed,
        elo_k=args.elo_k,
        show_matchups=not args.quiet_matchups,
    )
    _print_standings(standings)
    if not args.no_matrix:
        _print_pairwise_matrix(bots, pairs)
    if args.export_json:
        _export_json(
            args.export_json,
            game_name=args.game,
            bots=bots,
            standings=standings,
            pairs=pairs,
        )


if __name__ == "__main__":
    main()
