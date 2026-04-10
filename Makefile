.PHONY: tictactoe tictactoe-tree connect4 connect4-tree connect-four checkers dots dots-terminal pygame 2048 2048-play benchmark arena analyze help test

help:
	@echo "MCTSLab — run games or tests"
	@echo ""
	@echo "  make tictactoe      — Play Tic-tac-toe vs MCTS bot"
	@echo "  make tictactoe-tree — Play Tic-tac-toe with tree shown after each bot move"
	@echo "  make connect4       — Play Connect Four vs MCTS bot"
	@echo "  make connect4-tree  — Play Connect Four with tree shown after each bot move"
	@echo "  make checkers       — Play Checkers (6×6) vs MCTS bot"
	@echo "  make dots           — Play Dots and Boxes (Pygame GUI). Use SIMULATIONS=N for strength"
	@echo "  make dots-terminal  — Dots and Boxes in terminal"
	@echo "  make pygame         — Pygame GUI (tictactoe, connect4, dots)"
	@echo "  make 2048           — Watch MCTS play 2048 (1s delay between moves)"
	@echo "  make 2048-play      — Play 2048 yourself (W/A/S/D), optional HINT=N"
	@echo "  make benchmark      — MCTS vs random win-rate (tic-tac-toe, 50 games per side)"
	@echo "  make arena          — Round-robin arena with Elo (configurable bot specs)"
	@echo "  make analyze        — Position analyzer (set GAME/MOVES/SIMULATIONS)"
	@echo "  make test           — Run tests"
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

dots:
	python scripts/play_dots.py $(if $(SIMULATIONS),--simulations $(SIMULATIONS),)

dots-terminal:
	python scripts/play_dots.py --terminal

pygame:
	python scripts/pygame_ui.py --game tictactoe

2048:
	python scripts/play_2048.py

2048-play:
	python scripts/play_2048.py --play $(if $(HINT),--hint-simulations $(HINT),)

benchmark:
	python scripts/benchmark_vs_random.py

arena:
	python scripts/arena.py $(if $(GAME),--game $(GAME),) $(if $(BOTS),--bots $(BOTS),) $(if $(GAMES),--games-per-side $(GAMES),) $(if $(SEED),--seed $(SEED),)

analyze:
	python scripts/analyze_position.py $(if $(GAME),--game $(GAME),) $(if $(MOVES),--moves "$(MOVES)",) $(if $(SIMULATIONS),--simulations $(SIMULATIONS),)

test:
	python -m pytest tests/ -v
