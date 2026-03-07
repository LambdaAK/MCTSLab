#!/usr/bin/env python3
"""
Play Connect Four vs an MCTS bot. You are X (player 0), bot is O (player 1).
Moves: enter column 1–7 (left to right).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcts import run_mcts

from games.connect_four import ConnectFour, format_board, initial_state


def main() -> None:
    game = ConnectFour()
    state = initial_state()
    human = 0  # X
    bot = 1    # O
    num_simulations = 5000

    print("Connect Four — You are X, bot is O. Drop in column 1–7.")
    print()

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        print(format_board(state))
        print()

        if current == human:
            legal = game.get_legal_actions(state)
            legal_1 = [c + 1 for c in legal]
            while True:
                try:
                    s = input("Your move (column 1–7): ").strip()
                    move_1 = int(s)
                    if move_1 in legal_1:
                        break
                except ValueError:
                    pass
                print("Invalid. Legal columns:", legal_1)
            state = game.apply_action(state, move_1 - 1)
        else:
            print("Bot thinking...")
            _, action = run_mcts(game, state, num_simulations=num_simulations)
            if action is None:
                break
            state = game.apply_action(state, action)
            print(f"Bot drops in column {action + 1}\n")

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
