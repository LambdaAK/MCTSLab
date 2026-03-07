"""
MCTSLab — Monte Carlo Tree Search framework.

Use the Game protocol to implement any game, then run UCT with run_mcts().
"""

from mcts.game import ApplyResult, Game, Outcome, PlayerId
from mcts.node import Node
from mcts.rollout import rollout_until_terminal
from mcts.uct import one_uct_iteration, run_mcts

__all__ = [
    "Game",
    "PlayerId",
    "Outcome",
    "ApplyResult",
    "Node",
    "rollout_until_terminal",
    "one_uct_iteration",
    "run_mcts",
]
