#!/usr/bin/env python3
"""
Play Connect Four vs an MCTS bot. You are X (player 0), bot is O (player 1).
Moves: enter column 1–7 (left to right).
"""

from __future__ import annotations

import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcts import run_mcts

from games.connect_four import ConnectFour, format_board, initial_state

try:
    import ui
    use_rich = ui.is_rich_available()
except ImportError:
    use_rich = False


def show_board(state: tuple[int, ...]) -> None:
    if use_rich:
        ui.print_c4_board(state)
    else:
        print(format_board(state))
        print()


def main() -> None:
    game = ConnectFour()
    state = initial_state()
    human = 0
    bot = 1
    num_simulations = 5000

    if use_rich:
        ui.print_c4_welcome()
    else:
        print("Connect Four — You are X, bot is O. Drop in column 1–7.\n")

    while not game.is_terminal(state):
        current = game.get_current_player(state)
        show_board(state)

        if current == human:
            legal = game.get_legal_actions(state)
            legal_1 = [c + 1 for c in legal]
            while True:
                if use_rich:
                    ui.print_turn_prompt(legal_1, "c4")
                else:
                    print("Your move (column 1–7): ", end="")
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
                    print("Invalid. Legal columns:", legal_1)
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
                ui.print_bot_played(action + 1, "c4")
            else:
                print(f"Bot drops in column {action + 1}\n")

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
