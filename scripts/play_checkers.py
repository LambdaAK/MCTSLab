#!/usr/bin/env python3
"""
Play Checkers (6×6) vs an MCTS bot. You are ● (player 0), bot is ○ (player 1).
Moves: enter the number of your chosen move from the list.
"""

from __future__ import annotations

import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcts import run_mcts, run_flat_ucb, format_tree, tree_stats

from games.checkers import Checkers, format_board, initial_state, move_to_str

try:
    import ui
    use_rich = ui.is_rich_available()
except ImportError:
    use_rich = False


def show_board(state: tuple) -> None:
    if use_rich:
        ui.print_checkers_board(state)
    else:
        print(format_board(state))
        print()


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Play Checkers (6×6) vs MCTS bot")
    p.add_argument("--variant", choices=["uct", "flat_ucb"], default="uct")
    p.add_argument("--show-tree", action="store_true", help="Print MCTS tree after each bot move")
    p.add_argument("--tree-depth", type=int, default=2)
    p.add_argument("--simulations", type=int, default=3000, help="MCTS simulations per move")
    args = p.parse_args()

    game = Checkers()
    state = initial_state()
    human = 0
    bot = 1
    num_simulations = args.simulations
    show_tree = args.show_tree
    tree_depth = args.tree_depth
    use_flat_ucb = args.variant == "flat_ucb"
    run_bot = run_flat_ucb if use_flat_ucb else run_mcts
    action_to_str = lambda a: move_to_str(a) if a is not None else "?"

    if use_rich:
        ui.print_checkers_welcome()
    else:
        print("Checkers (6×6) — You are ● (red), bot is ○ (blue). Enter move number.\n")

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        show_board(state)

        if current == human:
            legal = game.get_legal_actions(state)
            if use_rich:
                ui.console.print("[bold]Legal moves:[/]")
                for i, m in enumerate(legal, 1):
                    ui.console.print(f"  [cyan]{i}[/]: {move_to_str(m)}")
                ui.console.print()
            else:
                print("Legal moves:")
                for i, m in enumerate(legal, 1):
                    print(f"  {i}: {move_to_str(m)}")
                print()

            legal_nums = list(range(1, len(legal) + 1))
            while True:
                if use_rich:
                    ui.console.print(f"[bold]Your move (1–{len(legal)}):[/] ", end="")
                else:
                    print(f"Your move (1–{len(legal)}): ", end="")
                try:
                    s = input().strip()
                    choice = int(s)
                    if choice in legal_nums:
                        break
                except ValueError:
                    pass
                if use_rich:
                    ui.console.print(f"[red]Invalid. Enter 1–{len(legal)}[/]")
                else:
                    print(f"Invalid. Enter 1–{len(legal)}")
            move = legal[choice - 1]
            state = game.apply_action(state, move)
        else:
            if use_rich:
                ui.print_bot_thinking()
            else:
                print("Bot thinking...")
            root, action = run_bot(game, state, num_simulations=num_simulations)
            if action is None:
                break
            state = game.apply_action(state, action)
            if use_rich:
                ui.console.print(f"[blue]Bot plays [bold]{move_to_str(action)}[/bold][/blue]\n")
            else:
                print(f"Bot plays {move_to_str(action)}\n")
            if show_tree:
                stats = tree_stats(root)
                print(f"[Tree: {stats['node_count']} nodes, depth={stats['max_depth']}]")
                print(format_tree(root, max_depth=tree_depth, action_to_str=action_to_str))
                print()

    show_board(state)
    outcome = game.get_outcome(state)
    if outcome[0] > outcome[1]:
        msg = "You win!"
    elif outcome[1] > outcome[0]:
        msg = "Bot wins!"
    else:
        msg = "Draw."
    if use_rich:
        ui.print_result(msg)
    else:
        print(msg)


if __name__ == "__main__":
    main()
