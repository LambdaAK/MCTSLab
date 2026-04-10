from __future__ import annotations

from mcts.analysis import format_root_action_table, principal_variation, root_action_stats
from mcts.node import Node


def test_root_action_stats_sorted_and_shares() -> None:
    root = Node(state="root", current_player=0)
    root.visits = 30

    a = Node(state="a", parent=root, action="A", current_player=1)
    a.visits = 12
    a.total_reward = 7.2
    root.children["A"] = a

    b = Node(state="b", parent=root, action="B", current_player=1)
    b.visits = 6
    b.total_reward = 4.2
    root.children["B"] = b

    c = Node(state="c", parent=root, action="C", current_player=1)
    c.visits = 0
    c.total_reward = 0.0
    root.children["C"] = c

    stats = root_action_stats(root, exploration=1.414)
    assert [s.action for s in stats] == ["A", "B", "C"]
    assert stats[0].visit_share == 12 / 18
    assert stats[1].visit_share == 6 / 18
    assert stats[2].visit_share == 0.0
    assert stats[0].ucb is not None
    assert stats[2].ucb is None


def test_principal_variation_follows_most_visited() -> None:
    root = Node(state="root", current_player=0)

    a = Node(state="a", parent=root, action="A", current_player=1)
    b = Node(state="b", parent=root, action="B", current_player=1)
    a.visits = 10
    b.visits = 4
    root.children["A"] = a
    root.children["B"] = b

    a1 = Node(state="a1", parent=a, action="A1", current_player=0)
    a2 = Node(state="a2", parent=a, action="A2", current_player=0)
    a1.visits = 3
    a2.visits = 8
    a.children["A1"] = a1
    a.children["A2"] = a2

    line = principal_variation(root, max_depth=4)
    assert line == ["A", "A2"]


def test_format_root_action_table_contains_headers() -> None:
    root = Node(state="root", current_player=0)
    root.visits = 10

    a = Node(state="a", parent=root, action=0, current_player=1)
    a.visits = 10
    a.total_reward = 7.0
    root.children[0] = a

    table = format_root_action_table(
        root,
        action_to_str=lambda action: f"move-{action + 1}",
    )
    assert "Action" in table
    assert "Visits" in table
    assert "move-1" in table
