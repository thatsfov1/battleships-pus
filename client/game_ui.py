"""Renderowanie plansz w terminalu oraz parsowanie wspolrzednych strzalu.

Plansze to listy wierszy (indeks y), kazdy wiersz to lista komorek (indeks x).
Wspolrzedne wejsciowe podaje sie jako kolumna+wiersz, np. "B5":
kolumna A..J -> x = 0..9, wiersz 1..10 -> y = 0..9.
"""

from __future__ import annotations

from typing import Optional

BOARD_SIZE = 10
COLS = "ABCDEFGHIJ"

_SYMBOLS = {
    "": ".",    # nieznane / puste
    "S": "#",   # wlasny statek
    "X": "X",   # trafienie
    "o": "o",   # pudlo
}


def _normalize(grid) -> list[list[str]]:
    norm = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    if not grid:
        return norm
    for y in range(min(BOARD_SIZE, len(grid))):
        row = grid[y]
        for x in range(min(BOARD_SIZE, len(row))):
            norm[y][x] = row[x] or ""
    return norm


def render_board(grid, title: str) -> str:
    norm = _normalize(grid)
    lines = [title]
    lines.append("    " + " ".join(COLS))
    for y in range(BOARD_SIZE):
        cells = " ".join(_SYMBOLS.get(norm[y][x], "?") for x in range(BOARD_SIZE))
        lines.append(f"{y + 1:>2}  {cells}")
    return "\n".join(lines)


def render_side_by_side(own, tracking) -> str:
    left = render_board(own, "TWOJA PLANSZA").splitlines()
    right = render_board(tracking, "PLANSZA PRZECIWNIKA").splitlines()
    width = max(len(l) for l in left)
    rows = []
    for i in range(max(len(left), len(right))):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        rows.append(f"{l:<{width}}     {r}")
    return "\n".join(rows)


def parse_coords(text: str) -> Optional[tuple[int, int]]:
    """Parsuje 'B5' / 'b 5' na (x, y). Zwraca None gdy niepoprawne."""
    if not text:
        return None
    t = text.strip().upper().replace(" ", "").replace(",", "")
    if len(t) < 2 or t[0] not in COLS:
        return None
    x = COLS.index(t[0])
    try:
        row = int(t[1:])
    except ValueError:
        return None
    y = row - 1
    if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
        return x, y
    return None


def coord_label(x: int, y: int) -> str:
    return f"{COLS[x]}{y + 1}"
