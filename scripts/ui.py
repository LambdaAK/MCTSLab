"""
Shared terminal UI for MCTSLab games (rich-based).
"""

from __future__ import annotations

from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def _ensure_rich() -> None:
    if not RICH_AVAILABLE:
        raise RuntimeError("Install 'rich' for the enhanced UI: pip install rich")


def is_rich_available() -> bool:
    return RICH_AVAILABLE


# --- Tic-tac-toe (state = 9-tuple, 0=empty, 1=X, 2=O) ---

def print_ttt_board(state: tuple[int, ...]) -> None:
    _ensure_rich()
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    for _ in range(3):
        table.add_column(justify="center")
    chars = {0: "·", 1: "X", 2: "O"}
    for r in range(3):
        row_cells = []
        for c in range(3):
            v = state[r * 3 + c]
            cell = chars.get(v, "?")
            if v == 1:
                row_cells.append(Text(cell, style="bold red"))
            elif v == 2:
                row_cells.append(Text(cell, style="bold blue"))
            else:
                row_cells.append(Text(cell, style="dim"))
        table.add_row(*row_cells)
    # Position hints 1-9
    table.add_row(Text("1", style="dim"), Text("2", style="dim"), Text("3", style="dim"))
    table.add_row(Text("4", style="dim"), Text("5", style="dim"), Text("6", style="dim"))
    table.add_row(Text("7", style="dim"), Text("8", style="dim"), Text("9", style="dim"))
    console.print(Panel(table, title="[bold]Tic-tac-toe[/bold]", border_style="cyan"))


def print_ttt_welcome() -> None:
    _ensure_rich()
    console.print()
    console.print(Panel(
        "[bold cyan]You are X[/], [bold blue]Bot is O[/].\n"
        "Enter a number [1–9] to play (positions as in the grid below).",
        title="Tic-tac-toe",
        border_style="cyan",
    ))
    console.print()


# --- Connect Four (state = 42-tuple, row-major, 6 rows × 7 cols) ---

def print_c4_board(state: tuple[int, ...]) -> None:
    _ensure_rich()
    ROWS, COLS = 6, 7
    table = Table(box=box.ROUNDED, show_header=True, padding=(0, 1))
    for c in range(COLS):
        table.add_column(str(c + 1), justify="center")
    chars = {0: "◦", 1: "●", 2: "○"}  # empty, X (filled), O (circle)
    for r in range(ROWS):
        row_cells = []
        for c in range(COLS):
            v = state[r * COLS + c]
            cell = chars.get(v, "?")
            if v == 1:
                row_cells.append(Text(cell, style="bold red"))
            elif v == 2:
                row_cells.append(Text(cell, style="bold blue"))
            else:
                row_cells.append(Text(cell, style="dim"))
        table.add_row(*row_cells)
    console.print(Panel(table, title="[bold]Connect Four[/bold]", border_style="cyan"))


def print_c4_welcome() -> None:
    _ensure_rich()
    console.print()
    console.print(Panel(
        "[bold cyan]You are ● (red)[/], [bold blue]Bot is ○ (blue)[/].\n"
        "Enter a column number [1–7] to drop your piece.",
        title="Connect Four",
        border_style="cyan",
    ))
    console.print()


# --- Shared ---

def print_turn_prompt(legal_1: list[int], game: str = "move") -> None:
    _ensure_rich()
    if game == "move":
        console.print(f"[bold]Your move (1–9):[/] ", end="")
    else:
        console.print(f"[bold]Your move (column 1–7):[/] ", end="")


def print_invalid(legal_1: list[int]) -> None:
    _ensure_rich()
    console.print(f"[red]Invalid. Legal: {legal_1}[/]")


def print_bot_thinking() -> None:
    _ensure_rich()
    console.print("[dim]Bot thinking…[/]")


def print_bot_played(move_1: int, game: str = "ttt") -> None:
    _ensure_rich()
    if game == "ttt":
        console.print(f"[blue]Bot plays [bold]{move_1}[/bold][/blue]\n")
    else:
        console.print(f"[blue]Bot drops in column [bold]{move_1}[/bold][/blue]\n")


def print_result(message: str, style: str = "bold green") -> None:
    _ensure_rich()
    console.print()
    console.print(Panel(f"[{style}]{message}[/]", border_style="green" if "win" in message.lower() or "Draw" in message else "yellow"))


# --- 2048 (state = (board_16_tuple, turn)) ---

def print_2048_board(state: tuple[tuple[int, ...], str]) -> None:
    _ensure_rich()
    board, _ = state
    SIZE = 4
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
    for _ in range(SIZE):
        table.add_column(justify="center")
    for r in range(SIZE):
        row_cells = []
        for c in range(SIZE):
            v = board[r * SIZE + c]
            s = str(v) if v else "·"
            if v >= 2048:
                row_cells.append(Text(s, style="bold yellow"))
            elif v >= 256:
                row_cells.append(Text(s, style="bold green"))
            elif v >= 32:
                row_cells.append(Text(s, style="cyan"))
            elif v:
                row_cells.append(Text(s, style="white"))
            else:
                row_cells.append(Text(s, style="dim"))
        table.add_row(*row_cells)
    console.print(Panel(table, title="[bold]2048[/bold]", border_style="yellow"))


def print_2048_watch_info(move_num: int, score: int, last_move: str | None) -> None:
    _ensure_rich()
    console.print(f"  [dim]Move {move_num}[/]  [bold]Score: {score}[/]  [dim]Last: {last_move or '—'}[/]")


# --- Checkers (state = (board_36_tuple, turn)) ---

def print_checkers_board(state: tuple[tuple[int, ...], int]) -> None:
    _ensure_rich()
    board, _ = state
    ROWS, COLS = 6, 6

    def is_dark(r: int, c: int) -> bool:
        return (r + c) % 2 == 1

    def get(r: int, c: int) -> int:
        return board[r * COLS + c] if 0 <= r < ROWS and 0 <= c < COLS else 0

    table = Table(box=box.ROUNDED, show_header=True, padding=(0, 1))
    table.add_column("", justify="right", style="dim", width=2)
    for c in range(COLS):
        table.add_column(chr(ord("a") + c), justify="center")
    chars = {0: "·", 1: "●", 2: "◆", 3: "○", 4: "◇"}
    for r in range(ROWS):
        row_cells = [Text(str(ROWS - r), style="dim")]
        for c in range(COLS):
            if is_dark(r, c):
                v = get(r, c)
                cell = chars.get(v, "?")
                if v in (1, 2):
                    row_cells.append(Text(cell, style="bold red"))
                elif v in (3, 4):
                    row_cells.append(Text(cell, style="bold blue"))
                else:
                    row_cells.append(Text(cell, style="dim"))
            else:
                row_cells.append(Text(" ", style="dim"))
        table.add_row(*row_cells)
    table.add_row(Text("", style="dim"), *[Text(chr(ord("a") + c), style="dim") for c in range(COLS)])
    console.print(Panel(table, title="[bold]Checkers (6×6)[/bold]", border_style="cyan"))


def print_checkers_welcome() -> None:
    _ensure_rich()
    console.print()
    console.print(Panel(
        "[bold cyan]You are ● (red)[/], [bold blue]Bot is ○ (blue)[/].\n"
        "Enter the number of your chosen move (1, 2, 3, …).",
        title="Checkers",
        border_style="cyan",
    ))
    console.print()
