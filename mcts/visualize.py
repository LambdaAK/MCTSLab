"""
MCTS tree visualization: ASCII view for the terminal and DOT export for Graphviz.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from mcts.node import Node


def format_tree(
    root: Node,
    *,
    max_depth: int = 2,
    max_children: int = 12,
    action_to_str: Optional[Callable[[Any], str]] = None,
) -> str:
    """
    Return an ASCII representation of the MCTS tree from root.

    Shows visits and mean reward per node. Limits depth and number of children
    per node to keep output readable.
    """
    action_str = action_to_str or (lambda a: str(a) if a is not None else "?")

    lines: list[str] = []

    def mean_reward(n: Node) -> str:
        if n.visits == 0:
            return "—"
        return f"{n.total_reward / n.visits:.3f}"

    def write_node(node: Node, indent: str, depth: int) -> None:
        if depth < 0:
            return
        if node.is_root():
            lines.append(f"{indent}root  visits={node.visits}  mean_reward={mean_reward(node)}")
        else:
            label = action_str(node.action)
            lines.append(
                f"{indent}→ {label}  visits={node.visits}  mean_reward={mean_reward(node)}"
            )
        if depth == 0:
            return
        children = list(node.children.values())
        if not children:
            return
        # Sort by visits descending, take top max_children
        children.sort(key=lambda n: n.visits, reverse=True)
        for child in children[:max_children]:
            write_node(child, indent + "  ", depth - 1)
        if len(children) > max_children:
            lines.append(f"{indent}  ... and {len(children) - max_children} more")

    write_node(root, "", max_depth)
    return "\n".join(lines)


def tree_stats(root: Node) -> dict[str, Any]:
    """Return basic stats about the tree: node count, max depth, root children."""
    node_count = 0
    max_d = 0

    def count(node: Node, depth: int) -> None:
        nonlocal node_count, max_d
        node_count += 1
        if depth > max_d:
            max_d = depth
        for child in node.children.values():
            count(child, depth + 1)

    count(root, 0)
    return {
        "node_count": node_count,
        "max_depth": max_d,
        "root_visits": root.visits,
        "num_children": len(root.children),
    }


def to_dot(
    root: Node,
    *,
    max_depth: int = 3,
    max_children_per_node: int = 20,
    action_to_str: Optional[Callable[[Any], str]] = None,
) -> str:
    """
    Return a DOT (Graphviz) source string for the MCTS tree.

    Pipe to `dot -Tpng -o tree.png` or use with other Graphviz tools.
    """
    action_str = action_to_str or (lambda a: str(a) if a is not None else "?")
    lines = ["digraph MCTS {", "  node [shape=box, fontname=sans];", "  edge [fontname=sans];"]

    node_id: dict[int, int] = {}
    counter = [0]

    def id_for(node: Node) -> int:
        i = id(node)
        if i not in node_id:
            node_id[i] = counter[0]
            counter[0] += 1
        return node_id[i]

    def escape(s: str) -> str:
        return s.replace('"', '\\"').replace("\n", "\\n")

    def add_node(node: Node, depth: int) -> None:
        if depth < 0:
            return
        nid = id_for(node)
        if node.visits > 0:
            mean = node.total_reward / node.visits
            label = f"visits={node.visits}\\nreward={mean:.3f}"
        else:
            label = "visits=0"
        if not node.is_root():
            label = f"{escape(action_str(node.action))}\\n{label}"
        else:
            label = f"root\\n{label}"
        lines.append(f'  n{nid} [label="{label}"];')
        if depth == 0:
            return
        children = list(node.children.values())
        children.sort(key=lambda n: n.visits, reverse=True)
        for child in children[:max_children_per_node]:
            cid = id_for(child)
            add_node(child, depth - 1)
            lines.append(f"  n{nid} -> n{cid};")
        if len(children) > max_children_per_node:
            # Placeholder for omitted children
            omit_id = counter[0]
            counter[0] += 1
            lines.append(f'  n{omit_id} [label="... {len(children) - max_children_per_node} more"];')
            lines.append(f"  n{nid} -> n{omit_id};")

    add_node(root, max_depth)
    lines.append("}")
    return "\n".join(lines)
