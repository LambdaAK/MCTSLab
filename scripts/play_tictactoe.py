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

from mcts import run_mcts

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
    game = TicTacToe()
    state = initial_state()
    human = 0
    bot = 1
    num_simulations = 2000

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
            _, action = run_mcts(game, state, num_simulations=num_simulations)
            if action is None:
                break
            state = game.apply_action(state, action)
            if use_rich:
                ui.print_bot_played(action + 1, "ttt")
            else:
                print(f"Bot plays {action + 1}\n")

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
