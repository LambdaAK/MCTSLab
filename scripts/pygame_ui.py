#!/usr/bin/env python3
"""
Pygame graphical interface for MCTSLab games.
Play Tic-tac-toe, Connect Four, or Dots and Boxes vs an MCTS bot.
"""

from __future__ import annotations

import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
import pygame

# Colors
BG = (28, 28, 36)
GRID = (60, 60, 80)
ACCENT = (100, 180, 255)
P1_COLOR = (255, 90, 90)   # Red (You)
P2_COLOR = (90, 140, 255)   # Blue (Bot)
TEXT = (240, 240, 250)
DIM = (120, 120, 140)
HOVER = (100, 130, 180)  # Brighter blue-gray for hover feedback

# Layout
CELL_SIZE = 80
MARGIN = 20
TITLE_H = 50
STATUS_H = 40


def run_pygame(game_name: str, num_simulations: int = 3000) -> None:
    pygame.init()
    pygame.display.set_caption(f"MCTSLab — {game_name}")

    if game_name == "tictactoe":
        from games.tictactoe import TicTacToe, initial_state
        game = TicTacToe()
        state = initial_state()
        renderer = TicTacToeRenderer()
    elif game_name == "connect4":
        from games.connect_four import ConnectFour, initial_state
        game = ConnectFour()
        state = initial_state()
        renderer = ConnectFourRenderer()
    elif game_name == "dots":
        from games.dots_and_boxes import DotsAndBoxes, initial_state
        game = DotsAndBoxes()
        state = initial_state()
        renderer = DotsAndBoxesRenderer()
    else:
        raise ValueError(f"Unknown game: {game_name}")

    from mcts import run_mcts, run_flat_ucb
    run_bot = run_mcts

    human = 0
    bot = 1
    status_msg = "Your turn"
    thinking = False
    bot_result: list = []  # [action] when done

    def run_bot_async() -> None:
        result = run_bot(game, state, num_simulations=num_simulations)
        bot_result.append(result)

    board_rect, board_offset = renderer.get_layout()
    w = board_rect.width + 2 * MARGIN
    h = TITLE_H + board_rect.height + STATUS_H + 2 * MARGIN
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    def redraw() -> None:
        screen.fill(BG)
        # Title
        font = pygame.font.Font(None, 36)
        title = font.render(f"{game_name.replace('_', ' ').title()} — You vs MCTS", True, TEXT)
        screen.blit(title, (MARGIN, MARGIN))
        # Board (with hover highlight for dots)
        if game_name == "dots":
            hover = None
            if not thinking and game.get_current_player(state) == human:
                legal = set(game.get_legal_actions(state))
                hover = renderer.click_to_action(pygame.mouse.get_pos(), board_offset, board_rect, legal_edges=legal)
            renderer.draw(screen, state, board_offset, board_rect, hover_edge=hover)
        else:
            renderer.draw(screen, state, board_offset, board_rect)
        # Status
        status = font.render(status_msg, True, TEXT)
        screen.blit(status, (MARGIN, h - MARGIN - STATUS_H))
        pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                h = event.h
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not thinking:
                if game.is_terminal(state):
                    running = False
                    break
                current = game.get_current_player(state)
                if current == human:
                    pos = pygame.mouse.get_pos()
                    action = renderer.click_to_action(pos, board_offset, board_rect)
                    if action is not None and action in game.get_legal_actions(state):
                        state = game.apply_action(state, action)
                        if game.get_current_player(state) == bot:
                            status_msg = "Bot thinking..."
                            thinking = True
                            bot_result.clear()
                            t = threading.Thread(target=run_bot_async)
                            t.daemon = True
                            t.start()
                        else:
                            status_msg = "Your turn"

        if thinking and bot_result:
            root, action = bot_result.pop()
            if action is not None:
                state = game.apply_action(state, action)
            thinking = False
            if game.is_terminal(state):
                outcome = game.get_outcome(state)
                if outcome[0] > outcome[1]:
                    status_msg = "You win!"
                elif outcome[1] > outcome[0]:
                    status_msg = "Bot wins!"
                else:
                    status_msg = "Draw."
            elif game.get_current_player(state) == bot:
                # Bot completed a box and gets another turn
                status_msg = "Bot thinking..."
                thinking = True
                bot_result.clear()
                t = threading.Thread(target=run_bot_async)
                t.daemon = True
                t.start()
            else:
                status_msg = "Your turn"

        if game.is_terminal(state) and not thinking:
            outcome = game.get_outcome(state)
            if outcome[0] > outcome[1]:
                status_msg = "You win!"
            elif outcome[1] > outcome[0]:
                status_msg = "Bot wins!"
            else:
                status_msg = "Draw."

        redraw()
        clock.tick(60)

    pygame.quit()


class TicTacToeRenderer:
    def get_layout(self) -> tuple[pygame.Rect, tuple[int, int]]:
        w = 3 * CELL_SIZE + 2 * 4
        h = 3 * CELL_SIZE + 2 * 4
        ox = MARGIN
        oy = TITLE_H + MARGIN
        return pygame.Rect(ox, oy, w, h), (ox, oy)

    def draw(self, screen: pygame.Surface, state: tuple, offset: tuple[int, int], rect: pygame.Rect) -> None:
        ox, oy = offset
        gap = 4
        for r in range(3):
            for c in range(3):
                x = ox + c * (CELL_SIZE + gap)
                y = oy + r * (CELL_SIZE + gap)
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, GRID, cell_rect)
                pygame.draw.rect(screen, DIM, cell_rect, 2)
                idx = r * 3 + c
                val = state[idx]
                if val == 1:
                    self._draw_x(screen, cell_rect, P1_COLOR)
                elif val == 2:
                    self._draw_o(screen, cell_rect, P2_COLOR)

    def _draw_x(self, screen: pygame.Surface, rect: pygame.Rect, color: tuple) -> None:
        pad = 12
        pygame.draw.line(screen, color, (rect.left + pad, rect.top + pad),
                         (rect.right - pad, rect.bottom - pad), 4)
        pygame.draw.line(screen, color, (rect.right - pad, rect.top + pad),
                         (rect.left + pad, rect.bottom - pad), 4)

    def _draw_o(self, screen: pygame.Surface, rect: pygame.Rect, color: tuple) -> None:
        pad = 12
        pygame.draw.circle(screen, color, rect.center, min(rect.w, rect.h) // 2 - pad, 4)

    def click_to_action(self, pos: tuple[int, int], offset: tuple[int, int], rect: pygame.Rect) -> int | None:
        ox, oy = offset
        gap = 4
        for r in range(3):
            for c in range(3):
                x = ox + c * (CELL_SIZE + gap)
                y = oy + r * (CELL_SIZE + gap)
                if x <= pos[0] < x + CELL_SIZE and y <= pos[1] < y + CELL_SIZE:
                    return r * 3 + c
        return None


class ConnectFourRenderer:
    ROWS = 6
    COLS = 7

    def get_layout(self) -> tuple[pygame.Rect, tuple[int, int]]:
        w = self.COLS * CELL_SIZE + (self.COLS - 1) * 4
        h = self.ROWS * CELL_SIZE + (self.ROWS - 1) * 4
        ox = MARGIN
        oy = TITLE_H + MARGIN
        return pygame.Rect(ox, oy, w, h), (ox, oy)

    def draw(self, screen: pygame.Surface, state: tuple, offset: tuple[int, int], rect: pygame.Rect) -> None:
        ox, oy = offset
        gap = 4
        for r in range(self.ROWS):
            for c in range(self.COLS):
                x = ox + c * (CELL_SIZE + gap)
                y = oy + r * (CELL_SIZE + gap)
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, GRID, cell_rect)
                pygame.draw.rect(screen, DIM, cell_rect, 2)
                idx = r * self.COLS + c
                val = state[idx]
                if val == 1:
                    pygame.draw.circle(screen, P1_COLOR, cell_rect.center, CELL_SIZE // 2 - 8)
                elif val == 2:
                    pygame.draw.circle(screen, P2_COLOR, cell_rect.center, CELL_SIZE // 2 - 8)

    def click_to_action(self, pos: tuple[int, int], offset: tuple[int, int], rect: pygame.Rect) -> int | None:
        ox, oy = offset
        gap = 4
        for c in range(self.COLS):
            x = ox + c * (CELL_SIZE + gap)
            if x <= pos[0] < x + CELL_SIZE and oy <= pos[1] < oy + rect.height:
                return c
        return None


class DotsAndBoxesRenderer:
    DOT_R = 8
    EDGE_THICK = 10
    HIT_MARGIN = 18
    GAP = 50  # Smaller gap for larger grid to fit on screen

    def __init__(self) -> None:
        from games.dots_and_boxes import ROWS, COLS, NUM_H_EDGES, NUM_EDGES
        self.ROWS = ROWS
        self.COLS = COLS
        self.NUM_H_EDGES = NUM_H_EDGES
        self.NUM_EDGES = NUM_EDGES

    def get_layout(self) -> tuple[pygame.Rect, tuple[int, int]]:
        gap = self.GAP
        w = self.COLS * gap + 2 * self.DOT_R
        h = self.ROWS * gap + 2 * self.DOT_R
        ox = MARGIN
        oy = TITLE_H + MARGIN
        return pygame.Rect(ox, oy, w, h), (ox, oy)

    def _edge_rect(self, edge_idx: int, ox: int, oy: int, gap: int) -> pygame.Rect:
        if edge_idx < self.NUM_H_EDGES:
            r = edge_idx // self.COLS
            c = edge_idx % self.COLS
            x = ox + c * gap
            y = oy + r * gap - self.EDGE_THICK // 2
            return pygame.Rect(x, y, gap, self.EDGE_THICK)
        else:
            v_idx = edge_idx - self.NUM_H_EDGES
            r = v_idx // (self.COLS + 1)
            c = v_idx % (self.COLS + 1)
            x = ox + c * gap - self.EDGE_THICK // 2
            y = oy + r * gap
            return pygame.Rect(x, y, self.EDGE_THICK, gap)

    def draw(self, screen: pygame.Surface, state: tuple, offset: tuple[int, int], rect: pygame.Rect, hover_edge: int | None = None) -> None:
        edges, _, score0, score1, _ = state
        ox, oy = offset
        gap = self.GAP

        # Draw edges
        for edge_idx in range(self.NUM_EDGES):
            r = self._edge_rect(edge_idx, ox, oy, gap)
            if edges[edge_idx] == 0:
                color = HOVER if edge_idx == hover_edge else DIM
                pygame.draw.rect(screen, color, r)
            elif edges[edge_idx] == 1:
                pygame.draw.rect(screen, P1_COLOR, r)
            else:
                pygame.draw.rect(screen, P2_COLOR, r)

        # Draw completed boxes
        from games.dots_and_boxes import _box_owner_from_state, _is_box_complete
        for br in range(self.ROWS):
            for bc in range(self.COLS):
                if _is_box_complete(edges, (br, bc)):
                    owner = _box_owner_from_state(state, br, bc)
                    if owner:
                        cx = ox + bc * gap + gap // 2
                        cy = oy + br * gap + gap // 2
                        color = P1_COLOR if owner == 1 else P2_COLOR
                        font = pygame.font.Font(None, 32)
                        label = font.render("X" if owner == 1 else "O", True, color)
                        trect = label.get_rect(center=(cx, cy))
                        screen.blit(label, trect)

        # Draw dots on top
        for dr in range(self.ROWS + 1):
            for dc in range(self.COLS + 1):
                x = ox + dc * gap
                y = oy + dr * gap
                pygame.draw.circle(screen, TEXT, (x, y), self.DOT_R)

        # Scores
        font = pygame.font.Font(None, 28)
        s = font.render(f"You: {score0}  Bot: {score1}", True, TEXT)
        screen.blit(s, (ox, oy - 28))

    def click_to_action(self, pos: tuple[int, int], offset: tuple[int, int], rect: pygame.Rect, legal_edges: set | None = None) -> int | None:
        ox, oy = offset
        gap = self.GAP
        mx, my = pos[0], pos[1]
        # Board bounds
        board_left = ox - self.HIT_MARGIN
        board_right = ox + self.COLS * gap + self.HIT_MARGIN
        board_top = oy - self.HIT_MARGIN
        board_bottom = oy + self.ROWS * gap + self.HIT_MARGIN
        if not (board_left <= mx <= board_right and board_top <= my <= board_bottom):
            return None
        # Find closest edge to click (optionally only among legal edges for hover)
        best_edge = None
        best_dist = float("inf")
        for edge_idx in range(self.NUM_EDGES):
            if legal_edges is not None and edge_idx not in legal_edges:
                continue
            r = self._edge_rect(edge_idx, ox, oy, gap)
            cx, cy = r.center
            dist = (mx - cx) ** 2 + (my - cy) ** 2
            if dist < best_dist and dist < (gap * 2) ** 2:
                best_dist = dist
                best_edge = edge_idx
        return best_edge


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Pygame interface for MCTSLab games")
    p.add_argument("--game", choices=["tictactoe", "connect4", "dots"], default="tictactoe")
    p.add_argument("--simulations", type=int, default=3000, help="MCTS simulations per bot move")
    args = p.parse_args()
    run_pygame(args.game, args.simulations)


if __name__ == "__main__":
    main()
