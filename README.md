# MCTSLab

A small MCTS framework in Python. You can play tic-tac-toe, Connect Four, or watch 2048; there’s a Flat UCB variant to compare against standard UCT, tree visualization, and a benchmark script that pits MCTS against a random player.

Python 3.9+ is enough to run everything. Install `rich` if you want the nicer terminal UI when playing games (`pip install rich`).

From the repo root, run `make help` to see commands. The main ones: `make tictactoe`, `make connect4`, `make 2048` to play or watch, and `make benchmark` to run the win-rate comparison. Use `--variant flat_ucb` or `--show-tree` on the play scripts if you want to try the other variant or see the search tree after each move.

Layout: `mcts/` has the core (game protocol, UCT, flat UCB, rollout, viz), `games/` has the three games, `scripts/` has the play and benchmark scripts. PLAN.md has the original design and notes on adding a new game.
