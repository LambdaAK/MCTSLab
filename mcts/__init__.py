"""
MCTSLab — Monte Carlo Tree Search framework.

Use the Game protocol to implement any game, then run UCT with run_mcts().
"""

from mcts.flat_ucb import run_flat_ucb
from mcts.game import ApplyResult, Game, Outcome, PlayerId
from mcts.node import Node
from mcts.rollout import rollout_until_terminal
from mcts.uct import one_uct_iteration, run_mcts
from mcts.visualize import format_tree, tree_stats, to_dot

__all__ = [
    "Game",
    "PlayerId",
    "Outcome",
    "ApplyResult",
    "Node",
    "rollout_until_terminal",
    "one_uct_iteration",
    "run_mcts",
    "run_flat_ucb",
    "format_tree",
    "tree_stats",
    "to_dot",
]
