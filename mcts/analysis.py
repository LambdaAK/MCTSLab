"""
Helpers for inspecting MCTS root decisions and principal variation lines.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Optional

from mcts.node import Node


@dataclass(frozen=True)
class RootActionStat:
    """Inspection stats for one root action."""

    action: Any
    visits: int
    mean_reward: float
    visit_share: float
    ucb: Optional[float]


def root_action_stats(root: Node, *, exploration: float = 1.414) -> list[RootActionStat]:
    """
    Return sorted stats for each root child.

    Sorting is by visits desc, then mean_reward desc.
    """
    if not root.children:
        return []

    total_child_visits = sum(child.visits for child in root.children.values())
    parent_log = math.log(root.visits + 1) if root.visits > 0 else 0.0

    stats: list[RootActionStat] = []
    for action, child in root.children.items():
        mean = child.total_reward / child.visits if child.visits else 0.0
        share = (child.visits / total_child_visits) if total_child_visits > 0 else 0.0
        if child.visits > 0 and root.visits > 0:
            ucb = mean + exploration * math.sqrt(parent_log / child.visits)
        else:
            ucb = None
        stats.append(
            RootActionStat(
                action=action,
                visits=child.visits,
                mean_reward=mean,
                visit_share=share,
                ucb=ucb,
            )
        )

    stats.sort(key=lambda s: (s.visits, s.mean_reward), reverse=True)
    return stats


def principal_variation(root: Node, *, max_depth: int = 8) -> list[Any]:
    """
    Follow most-visited children from root and return the action sequence.
    """
    if max_depth <= 0:
        return []

    line: list[Any] = []
    node = root
    for _ in range(max_depth):
        child = node.most_visited_child()
        if child is None:
            break
        line.append(child.action)
        node = child
    return line


def format_root_action_table(
    root: Node,
    *,
    top_n: int = 8,
    exploration: float = 1.414,
    action_to_str: Optional[Callable[[Any], str]] = None,
) -> str:
    """
    Return a compact plain-text table of root action quality.
    """
    action_fmt = action_to_str or (lambda a: str(a))
    stats = root_action_stats(root, exploration=exploration)
    if not stats:
        return "(no expanded root actions)"

    if top_n > 0:
        stats = stats[:top_n]

    rows: list[list[str]] = []
    for s in stats:
        rows.append(
            [
                action_fmt(s.action),
                str(s.visits),
                f"{100.0 * s.visit_share:5.1f}%",
                f"{s.mean_reward:.3f}",
                "—" if s.ucb is None else f"{s.ucb:.3f}",
            ]
        )

    headers = ["Action", "Visits", "Share", "Mean", "UCB"]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def format_row(cells: list[str]) -> str:
        return (
            f"{cells[0]:<{widths[0]}}  "
            f"{cells[1]:>{widths[1]}}  "
            f"{cells[2]:>{widths[2]}}  "
            f"{cells[3]:>{widths[3]}}  "
            f"{cells[4]:>{widths[4]}}"
        )

    out: list[str] = []
    out.append(format_row(headers))
    out.append(
        f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}  {'-' * widths[3]}  {'-' * widths[4]}"
    )
    for row in rows:
        out.append(format_row(row))
    return "\n".join(out)
