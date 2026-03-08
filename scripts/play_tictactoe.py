#!/usr/bin/env python3
"""
Play Tic-tac-toe vs an MCTS bot. You are X (player 0), bot is O (player 1).
Moves: enter 1-9 (left-to-right, top-to-bottom).
"""

from __future__ import annotations

import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcts import run_mcts, run_flat_ucb, format_tree, tree_stats

from games.tictactoe import TicTacToe, format_board, initial_state

try:
    import ui
    use_rich = ui.is_rich_available()
except ImportError:
    use_rich = False


def show_board(state: tuple[int, ...]) -> None:
    if use_rich:
        ui.print_ttt_board(state)
    else:
        print(format_board(state))
        print("  1 2 3\n  4 5 6\n  7 8 9")
        print()


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Play Tic-tac-toe vs MCTS bot")
    p.add_argument("--variant", choices=["uct", "flat_ucb"], default="uct", help="MCTS variant: uct (full tree) or flat_ucb (root-only bandit)")
    p.add_argument("--show-tree", action="store_true", help="Print MCTS tree after each bot move")
    p.add_argument("--tree-depth", type=int, default=2, help="Depth of tree to show (default 2)")
    p.add_argument("--simulations", type=int, default=2000, help="MCTS simulations per bot move")
    args = p.parse_args()

    game = TicTacToe()
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
        ui.print_ttt_welcome()
    else:
        print("Tic-tac-toe — You are X, bot is O. Moves: 1-9 (row-major).")
        print("Board positions:  1 2 3 | 4 5 6 | 7 8 9\n")

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        show_board(state)

        if current == human:
            legal = game.get_legal_actions(state)
            legal_1 = [m + 1 for m in legal]
            while True:
                if use_rich:
                    ui.print_turn_prompt(legal_1, "move")
                else:
                    print("Your move (1-9): ", end="")
                try:
                    s = input().strip()
                    move_1 = int(s)
                    if move_1 in legal_1:
                        break
                except ValueError:
                    pass
                if use_rich:
                    ui.print_invalid(legal_1)
                else:
                    print("Invalid. Legal moves:", legal_1)
            state = game.apply_action(state, move_1 - 1)
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
                ui.print_bot_played(action + 1, "ttt")
            else:
                print(f"Bot plays {action + 1}\n")
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
