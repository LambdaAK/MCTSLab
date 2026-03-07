#!/usr/bin/env python3
"""
Run MCTS for a few simulations and show the tree (ASCII + optional DOT file).
Example: python scripts/show_tree.py
         python scripts/show_tree.py --game connect4 --simulations 500 --dot tree.dot
"""

from __future__ import annotations

import argparse
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from mcts import run_mcts, format_tree, tree_stats, to_dot


def main() -> None:
    p = argparse.ArgumentParser(description="Run MCTS and visualize the tree")
    p.add_argument("--game", choices=["tictactoe", "connect4"], default="tictactoe")
    p.add_argument("--simulations", type=int, default=100)
    p.add_argument("--depth", type=int, default=2, help="Tree depth to show in ASCII")
    p.add_argument("--dot", type=str, default=None, help="Write DOT to this file (e.g. tree.dot)")
    args = p.parse_args()

    if args.game == "tictactoe":
        from games.tictactoe import TicTacToe, initial_state
        game = TicTacToe()
        state = initial_state()
        action_to_str = lambda a: str(a + 1) if a is not None else "?"
    else:
        from games.connect_four import ConnectFour, initial_state
        game = ConnectFour()
        state = initial_state()
        action_to_str = lambda a: str(a + 1) if a is not None else "?"

    print(f"Running {args.simulations} simulations ({args.game})...")
    root, best_action = run_mcts(game, state, num_simulations=args.simulations)
    stats = tree_stats(root)
    print(f"Tree: {stats['node_count']} nodes, max_depth={stats['max_depth']}, root_visits={stats['root_visits']}")
    print(f"Best action: {best_action}")
    print()
    print("Tree (ASCII):")
    print(format_tree(root, max_depth=args.depth, action_to_str=action_to_str))

    if args.dot:
        dot_src = to_dot(root, max_depth=args.depth, action_to_str=action_to_str)
        with open(args.dot, "w") as f:
            f.write(dot_src)
        print(f"\nDOT written to {args.dot}. Render with: dot -Tpng -o tree.png {args.dot}")


if __name__ == "__main__":
    main()
