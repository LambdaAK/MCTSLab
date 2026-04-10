# MCTSLab

A small MCTS framework in Python. You can play tic-tac-toe, Connect Four, Checkers (6×6), Dots and Boxes, or watch 2048; there’s a Flat UCB variant to compare against standard UCT, tree visualization, and benchmark tooling.

Python 3.9+ is enough to run everything. Install `rich` for the nicer terminal UI (`pip install rich`), or `pygame` for the graphical interface (`pip install pygame`).

From the repo root, run `make help` to see commands. The main ones: `make tictactoe`, `make connect4`, `make checkers`, `make dots`, `make 2048` to play or watch, `make 2048-play` to play 2048 yourself, `make benchmark` for MCTS vs random, `make arena` for round-robin bot leagues with Elo + pairwise matrix, and `make analyze` for deep position analysis. Use `make pygame` for a graphical interface (Tic-tac-toe by default; `python scripts/pygame_ui.py --game connect4` or `--game dots` for others). Use `--variant flat_ucb` or `--show-tree` on the play scripts if you want to try the other variant or see the search tree after each move. Use `--simulations N` to control MCTS strength (e.g. `make dots SIMULATIONS=5000` or `python scripts/play_dots.py --simulations 5000`).

Quick examples:
- `python scripts/arena.py --game connect4 --bots uct:800 uct:2500 flat_ucb:2500 random`
- `python scripts/arena.py --game checkers --export-json out/checkers_arena.json`
- `python scripts/analyze_position.py --game tictactoe --moves "5 1 9" --simulations 5000`
- `make analyze GAME=connect4 MOVES="4 4 3 3 2" SIMULATIONS=6000`
- `python scripts/play_connect_four.py --coach-simulations 800 --explain-bot`
- `python scripts/play_2048.py --play --hint-simulations 400`

Layout: `mcts/` has the core (game protocol, UCT, flat UCB, rollout, viz), `games/` has the five games, `scripts/` has the play and benchmark scripts. PLAN.md has the original design and notes on adding a new game.
