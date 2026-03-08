#!/usr/bin/env python3
"""
Play Dots and Boxes vs an MCTS bot. You are X (player 0), bot is O (player 1).
Claim edges by entering 1–N (1-based; see board for numbering).
"""

from __future__ import annotations

import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcts import run_mcts, run_flat_ucb, format_tree, tree_stats

from games.dots_and_boxes import DotsAndBoxes, format_board, initial_state, NUM_EDGES

try:
    import ui
    use_rich = ui.is_rich_available()
except ImportError:
    use_rich = False


def show_board(state) -> None:
    if use_rich:
        ui.print_dots_board(state)
    else:
        print(format_board(state))
        print()


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Play Dots and Boxes vs MCTS bot")
    p.add_argument("--variant", choices=["uct", "flat_ucb"], default="uct")
    p.add_argument("--show-tree", action="store_true", help="Print MCTS tree after each bot move")
    p.add_argument("--tree-depth", type=int, default=2)
    p.add_argument("--simulations", type=int, default=7000, help="MCTS simulations per move")
    args = p.parse_args()

    game = DotsAndBoxes()
    state = initial_state()
    human = 0
    bot = 1
    num_simulations = args.simulations
    show_tree = args.show_tree
    tree_depth = args.tree_depth
    use_flat_ucb = args.variant == "flat_ucb"
    run_bot = run_flat_ucb if use_flat_ucb else run_mcts
    action_to_str = lambda a: str(a + 1) if a is not None else "?"

    if use_rich:
        ui.print_dots_welcome()
    else:
        print(f"Dots and Boxes — You are X, bot is O. Enter 1–{NUM_EDGES} to claim an edge.\n")

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        show_board(state)

        if current == human:
            legal = game.get_legal_actions(state)
            legal_display = [e + 1 for e in legal]
            while True:
                if use_rich:
                    ui.print_turn_prompt(legal_display, "dots")
                else:
                    print(f"Your move (1–{NUM_EDGES}): ", end="")
                try:
                    s = input().strip()
                    move_1 = int(s)
                    move = move_1 - 1
                    if move in legal:
                        break
                except ValueError:
                    pass
                if use_rich:
                    ui.print_invalid(legal_display)
                else:
                    print("Invalid. Legal edges:", sorted(legal_display))
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
                ui.print_bot_played(action + 1, "dots")
            else:
                print(f"Bot claims edge {action + 1}\n")
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
