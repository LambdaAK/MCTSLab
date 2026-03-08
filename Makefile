.PHONY: tictactoe tictactoe-tree connect4 connect4-tree connect-four checkers 2048 benchmark help test

help:
	@echo "MCTSLab — run games or tests"
	@echo ""
	@echo "  make tictactoe      — Play Tic-tac-toe vs MCTS bot"
	@echo "  make tictactoe-tree — Play Tic-tac-toe with tree shown after each bot move"
	@echo "  make connect4       — Play Connect Four vs MCTS bot"
	@echo "  make connect4-tree  — Play Connect Four with tree shown after each bot move"
	@echo "  make checkers      — Play Checkers (6×6) vs MCTS bot"
	@echo "  make 2048       — Watch MCTS play 2048 (1s delay between moves)"
	@echo "  make benchmark  — MCTS vs random win-rate (tic-tac-toe, 50 games per side)"
	@echo "  make test       — Run tests"
	@echo ""

tictactoe:
	python scripts/play_tictactoe.py

tictactoe-tree:
	python scripts/play_tictactoe.py --show-tree

connect4 connect-four:
	python scripts/play_connect_four.py

connect4-tree:
	python scripts/play_connect_four.py --show-tree

checkers:
	python scripts/play_checkers.py

2048:
	python scripts/play_2048.py

benchmark:
	python scripts/benchmark_vs_random.py

test:
	python -m pytest tests/ -v
