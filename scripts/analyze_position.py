#!/usr/bin/env python3
"""
Analyze an MCTS position for one game and print a ranked root-action report.

Examples:
  python scripts/analyze_position.py --game tictactoe --moves "5 1 9"
  python scripts/analyze_position.py --game connect4 --moves "4,4,3,3,2"
  python scripts/analyze_position.py --game checkers --moves "b6-a5,e1-f2"
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Any, Callable

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from mcts import (
    format_root_action_table,
    format_tree,
    principal_variation,
    run_flat_ucb,
    run_mcts,
    tree_stats,
)


GameFormatter = Callable[[Any], str]
ActionFormatter = Callable[[Any], str]
ActionParser = Callable[[str], Any]


def _split_tokens(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [tok for tok in raw.replace(",", " ").split() if tok]


def _load_game(
    game_name: str,
) -> tuple[Any, Any, GameFormatter, ActionFormatter, ActionParser, str]:
    if game_name == "tictactoe":
        from games.tictactoe import TicTacToe, format_board, initial_state

        game = TicTacToe()
        parser = lambda s: int(s) - 1
        return (
            game,
            initial_state(),
            format_board,
            lambda a: str(a + 1) if a is not None else "?",
            parser,
            "1-9",
        )

    if game_name == "connect4":
        from games.connect_four import ConnectFour, format_board, initial_state

        game = ConnectFour()
        parser = lambda s: int(s) - 1
        return (
            game,
            initial_state(),
            format_board,
            lambda a: str(a + 1) if a is not None else "?",
            parser,
            "1-7",
        )

    if game_name == "dots":
        from games.dots_and_boxes import DotsAndBoxes, format_board, initial_state, NUM_EDGES

        game = DotsAndBoxes()
        parser = lambda s: int(s) - 1
        return (
            game,
            initial_state(),
            format_board,
            lambda a: str(a + 1) if a is not None else "?",
            parser,
            f"1-{NUM_EDGES}",
        )

    if game_name == "checkers":
        from games.checkers import Checkers, format_board, initial_state, move_to_str, parse_move

        game = Checkers()

        def parse_checkers(token: str) -> Any:
            move = parse_move(token)
            if move is None:
                raise ValueError(f"invalid checkers move '{token}'")
            return move

        return (
            game,
            initial_state(),
            format_board,
            lambda a: move_to_str(a) if a is not None else "?",
            parse_checkers,
            "checkers notation (e.g. b6-a5, c4xe2)",
        )

    raise ValueError(f"unknown game: {game_name}")


def _apply_moves(
    game: Any,
    state: Any,
    move_tokens: list[str],
    parse_action: ActionParser,
    action_to_str: ActionFormatter,
) -> Any:
    for i, token in enumerate(move_tokens, 1):
        try:
            action = parse_action(token)
        except Exception as exc:
            raise ValueError(f"could not parse move #{i} '{token}': {exc}") from exc
        legal = game.get_legal_actions(state)
        if action not in legal:
            sample = ", ".join(action_to_str(a) for a in legal[:10])
            extra = "" if len(legal) <= 10 else ", ..."
            raise ValueError(
                f"illegal move #{i} '{token}'. Legal sample: {sample}{extra}"
            )
        result = game.apply_action(state, action)
        if isinstance(result, list):
            raise ValueError(
                "stochastic transitions encountered while applying moves; "
                "this analyzer expects deterministic move sequences"
            )
        state = result
    return state


def main() -> None:
    p = argparse.ArgumentParser(description="Analyze a position with MCTS and inspect root policy")
    p.add_argument("--game", choices=["tictactoe", "connect4", "checkers", "dots"], default="tictactoe")
    p.add_argument(
        "--moves",
        type=str,
        default="",
        help="Move list from initial state (space/comma separated). "
        "Example: '5 1 9' (TTT) or 'b6-a5,e1-f2' (checkers)",
    )
    p.add_argument("--variant", choices=["uct", "flat_ucb"], default="uct")
    p.add_argument("--simulations", type=int, default=4000)
    p.add_argument("--exploration", type=float, default=1.414)
    p.add_argument("--top", type=int, default=8, help="Show top-N root actions (0 = all)")
    p.add_argument("--pv-depth", type=int, default=8, help="Principal variation depth")
    p.add_argument("--show-tree", action="store_true", help="Print ASCII tree summary")
    p.add_argument("--tree-depth", type=int, default=2)
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    try:
        game, state, format_state, action_to_str, parse_action, move_hint = _load_game(args.game)
        tokens = _split_tokens(args.moves)
        if tokens:
            state = _apply_moves(game, state, tokens, parse_action, action_to_str)
    except ValueError as exc:
        p.error(str(exc))

    run_bot = run_flat_ucb if args.variant == "flat_ucb" else run_mcts
    rng = random.Random(args.seed)

    print(f"Game: {args.game} | Variant: {args.variant} | Simulations: {args.simulations}")
    if tokens:
        print(f"Applied moves ({move_hint}): {' '.join(tokens)}")
    print(f"Current player: {game.get_current_player(state)}")
    print()
    print("Position:")
    print(format_state(state))
    print()

    root, best_action = run_bot(
        game,
        state,
        num_simulations=args.simulations,
        exploration=args.exploration,
        rng=rng,
    )

    stats = tree_stats(root)
    print(
        "Tree stats: "
        f"nodes={stats['node_count']} "
        f"depth={stats['max_depth']} "
        f"root_visits={stats['root_visits']} "
        f"root_children={stats['num_children']}"
    )

    if best_action is None:
        print("Best action: <none>")
    else:
        print(f"Best action: {action_to_str(best_action)}")
    print()

    print("Top root actions:")
    print(
        format_root_action_table(
            root,
            top_n=args.top,
            exploration=args.exploration,
            action_to_str=action_to_str,
        )
    )
    print()

    pv = principal_variation(root, max_depth=args.pv_depth)
    if pv:
        print("Principal variation:")
        print("  " + " -> ".join(action_to_str(a) for a in pv))
    else:
        print("Principal variation: <empty>")

    if args.show_tree:
        print()
        print("Tree (ASCII):")
        print(format_tree(root, max_depth=args.tree_depth, action_to_str=action_to_str))


if __name__ == "__main__":
    main()
