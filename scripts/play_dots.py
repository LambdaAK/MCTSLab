#!/usr/bin/env python3
"""
Launch Dots and Boxes: tries Pygame GUI first, falls back to terminal if unavailable.
"""

from __future__ import annotations

import os
import subprocess
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, repo_root)
sys.path.insert(0, scripts_dir)


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Play Dots and Boxes")
    p.add_argument("--terminal", action="store_true", help="Force terminal UI (skip Pygame)")
    p.add_argument("--simulations", type=int, default=7000, help="MCTS simulations per bot move")
    args = p.parse_args()

    if not args.terminal:
        try:
            import pygame  # noqa: F401
            from pygame_ui import run_pygame
            run_pygame("dots", num_simulations=args.simulations)
            return
        except ImportError:
            print("Pygame not installed. Using terminal UI. (pip install pygame for GUI)")
        except Exception as e:
            print(f"Pygame failed to start: {e}")
            print("Falling back to terminal UI...")

    # Terminal fallback
    subprocess.run(
        [sys.executable, os.path.join(scripts_dir, "play_dots_and_boxes.py"), "--simulations", str(args.simulations)],
        cwd=repo_root,
    )


if __name__ == "__main__":
    main()
