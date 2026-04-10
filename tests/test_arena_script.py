from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_arena_module():
    here = Path(__file__).resolve().parent
    arena_path = here.parent / "scripts" / "arena.py"
    spec = importlib.util.spec_from_file_location("arena_script", arena_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_bot_spec_variants() -> None:
    arena = _load_arena_module()

    b1 = arena.parse_bot_spec("random")
    assert b1.name == "random"
    assert b1.variant == "random"
    assert b1.simulations == 0

    b2 = arena.parse_bot_spec("fast=flat:250")
    assert b2.name == "fast"
    assert b2.variant == "flat_ucb"
    assert b2.simulations == 250


def test_run_arena_returns_pairs() -> None:
    arena = _load_arena_module()
    bots = [arena.parse_bot_spec("uct:30"), arena.parse_bot_spec("random")]
    standings, pairs = arena.run_arena(
        "tictactoe",
        bots,
        games_per_side=1,
        exploration=1.414,
        seed=0,
        elo_k=16.0,
        show_matchups=False,
    )

    assert len(standings) == 2
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair.games == 2
    assert pair.bot_a == bots[0].name
    assert pair.bot_b == bots[1].name
