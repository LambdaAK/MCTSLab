#!/usr/bin/env python3
"""
Play Tic-tac-toe vs an MCTS bot. You are X (player 0), bot is O (player 1).
Moves: enter 0-8 (left-to-right, top-to-bottom).
"""

from __future__ import annotations

import os
import sys

# Allow importing from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcts import run_mcts

from games.tictactoe import TicTacToe, format_board, initial_state


def main() -> None:
    game = TicTacToe()
    state = initial_state()
    human = 0  # X
    bot = 1    # O
    num_simulations = 2000

    print("Tic-tac-toe — You are X, bot is O. Moves: 0-8 (row-major).")
    print("Board positions:\n  0 1 2\n  3 4 5\n  6 7 8\n")

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        print(format_board(state))
        print()

        if current == human:
            legal = game.get_legal_actions(state)
            while True:
                try:
                    s = input("Your move (0-8): ").strip()
                    move = int(s)
                    if move in legal:
                        break
                except ValueError:
                    pass
                print("Invalid. Legal moves:", legal)
            state = game.apply_action(state, move)
        else:
            print("Bot thinking...")
            _, action = run_mcts(game, state, num_simulations=num_simulations)
            if action is None:
                break
            state = game.apply_action(state, action)
            print(f"Bot plays {action}\n")

    print(format_board(state))
    outcome = game.get_outcome(state)
    if outcome[0] > outcome[1]:
        print("You win!")
    elif outcome[1] > outcome[0]:
        print("Bot wins!")
    else:
        print("Draw.")


if __name__ == "__main__":
    main()
