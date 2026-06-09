"""Silnik gry Statki: plansza, flota i rozstrzyganie strzalow.

Logika czysto obliczeniowa, niezalezna od sieci i protokolu. Plansza ma
rozmiar BOARD_SIZE x BOARD_SIZE, wspolrzedne (x, y) liczone od 0.
Flota rozstawiana jest losowo przez serwer (protokol nie ma komunikatu
rozstawiania statkow).
"""

from __future__ import annotations

import random
from typing import Final, Optional

BOARD_SIZE: Final[int] = 10
# 5 statkow: jeden 4-masztowy, trzy 3-masztowe, jeden 2-masztowy.
FLEET_SIZES: Final[tuple[int, ...]] = (4, 3, 3, 3, 2)

RESULT_MISS: Final[str] = "MISS"
RESULT_HIT: Final[str] = "HIT"
RESULT_SUNK: Final[str] = "SUNK"

MAX_PLACEMENT_ATTEMPTS: Final[int] = 1000


class Ship:
    """Pojedynczy statek jako zbior zajmowanych pol i pol trafionych."""

    def __init__(self, cells: set[tuple[int, int]]):
        self.cells: set[tuple[int, int]] = set(cells)
        self.hits: set[tuple[int, int]] = set()

    def register_hit(self, cell: tuple[int, int]) -> None:
        if cell in self.cells:
            self.hits.add(cell)

    def is_sunk(self) -> bool:
        return self.cells == self.hits


class Board:
    """Plansza jednego gracza wraz z flota i histroia strzalow przeciwnika."""

    def __init__(self, size: int = BOARD_SIZE):
        self.size = size
        self.ships: list[Ship] = []
        self._occupied: set[tuple[int, int]] = set()
        self.shots: set[tuple[int, int]] = set()
        self.last_sunk_len: int = 0  # dlugosc ostatnio zatopionego statku

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def already_shot(self, x: int, y: int) -> bool:
        return (x, y) in self.shots

    def place_fleet(self, sizes: tuple[int, ...] = FLEET_SIZES, rng: Optional[random.Random] = None) -> None:
        """Losowo rozstawia statki o podanych dlugosciach bez stykania sie."""
        generator = rng if rng is not None else random.Random()
        self.ships.clear()
        self._occupied.clear()

        for length in sizes:
            cells = self._find_placement(length, generator)
            if cells is None:
                raise RuntimeError("Nie udalo sie rozstawic floty na planszy.")
            ship = Ship(cells)
            self.ships.append(ship)
            self._occupied.update(cells)

    def _find_placement(self, length: int, generator: random.Random) -> Optional[set[tuple[int, int]]]:
        for _ in range(MAX_PLACEMENT_ATTEMPTS):
            horizontal = generator.choice([True, False])
            if horizontal:
                x = generator.randint(0, self.size - length)
                y = generator.randint(0, self.size - 1)
                cells = {(x + i, y) for i in range(length)}
            else:
                x = generator.randint(0, self.size - 1)
                y = generator.randint(0, self.size - length)
                cells = {(x, y + i) for i in range(length)}

            if self._is_free(cells):
                return cells
        return None

    def _is_free(self, cells: set[tuple[int, int]]) -> bool:
        """Pole jest wolne, gdy ani ono, ani jego sasiedzi nie sa zajete."""
        for (cx, cy) in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (cx + dx, cy + dy) in self._occupied:
                        return False
        return True

    @staticmethod
    def _is_straight_line(cells: set[tuple[int, int]]) -> bool:
        """Sprawdza, czy pola tworza ciagla, prosta linie (poziom lub pion)."""
        n = len(cells)
        if n == 0:
            return False
        if n == 1:
            return True
        xs = {x for (x, _) in cells}
        ys = {y for (_, y) in cells}
        if len(ys) == 1:
            return len(xs) == n and max(xs) - min(xs) == n - 1
        if len(xs) == 1:
            return len(ys) == n and max(ys) - min(ys) == n - 1
        return False

    def place_fleet_manual(self, ships, sizes: tuple[int, ...] = FLEET_SIZES) -> bool:
        """Ustawia flote z reczanego rozmieszczenia. Zwraca False, gdy uklad jest
        niepoprawny: zle rozmiary, poza plansza, nie-prosty statek, nakladanie
        lub stykanie sie statkow krawedzia/rogiem."""
        parsed: list[set[tuple[int, int]]] = []
        for cells in ships:
            try:
                cellset = {(int(x), int(y)) for (x, y) in cells}
            except (TypeError, ValueError):
                return False
            if len(cellset) != len(list(cells)):
                return False
            if not all(self.in_bounds(x, y) for (x, y) in cellset):
                return False
            if not self._is_straight_line(cellset):
                return False
            parsed.append(cellset)

        if sorted(len(c) for c in parsed) != sorted(sizes):
            return False

        occupied: set[tuple[int, int]] = set()
        for cellset in parsed:
            for (cx, cy) in cellset:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (cx + dx, cy + dy) in occupied:
                            return False
            occupied |= cellset

        self.ships = [Ship(c) for c in parsed]
        self._occupied = occupied
        self.shots = set()
        self.last_sunk_len = 0
        return True

    def receive_shot(self, x: int, y: int) -> str:
        """Rejestruje strzal przeciwnika i zwraca MISS / HIT / SUNK.
        Po zatopieniu ustawia last_sunk_len na dlugosc zatopionego statku."""
        self.shots.add((x, y))
        for ship in self.ships:
            if (x, y) in ship.cells:
                ship.register_hit((x, y))
                if ship.is_sunk():
                    self.last_sunk_len = len(ship.cells)
                    return RESULT_SUNK
                return RESULT_HIT
        return RESULT_MISS

    def all_sunk(self) -> bool:
        return bool(self.ships) and all(ship.is_sunk() for ship in self.ships)

    def own_view(self) -> list[list[str]]:
        """Widok wlasnej planszy: S=statek, X=trafiony, o=pudlo, ''=puste."""
        grid = [["" for _ in range(self.size)] for _ in range(self.size)]
        for (x, y) in self._occupied:
            grid[y][x] = "S"
        for ship in self.ships:
            for (x, y) in ship.hits:
                grid[y][x] = "X"
        for (x, y) in self.shots:
            if (x, y) not in self._occupied:
                grid[y][x] = "o"
        return grid

    def tracking_view(self) -> list[list[str]]:
        """Widok planszy przeciwnika dla atakujacego: X=trafienie, o=pudlo."""
        grid = [["" for _ in range(self.size)] for _ in range(self.size)]
        hit_cells = {cell for ship in self.ships for cell in ship.hits}
        for (x, y) in self.shots:
            grid[y][x] = "X" if (x, y) in hit_cells else "o"
        return grid
