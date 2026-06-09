import random
import unittest

from server import game
from server.game import Board, Ship


class TestShip(unittest.TestCase):
    def test_ship_sinks_only_when_all_cells_hit(self):
        ship = Ship({(0, 0), (1, 0), (2, 0)})
        ship.register_hit((0, 0))
        ship.register_hit((1, 0))
        self.assertFalse(ship.is_sunk())
        ship.register_hit((2, 0))
        self.assertTrue(ship.is_sunk())

    def test_register_hit_ignores_foreign_cell(self):
        ship = Ship({(0, 0)})
        ship.register_hit((5, 5))
        self.assertFalse(ship.is_sunk())


class TestBoard(unittest.TestCase):
    def test_place_fleet_creates_correct_number_and_sizes(self):
        board = Board()
        board.place_fleet(rng=random.Random(42))
        self.assertEqual(len(board.ships), len(game.FLEET_SIZES))
        sizes = sorted(len(ship.cells) for ship in board.ships)
        self.assertEqual(sizes, sorted(game.FLEET_SIZES))

    def test_placed_ships_do_not_touch(self):
        board = Board()
        board.place_fleet(rng=random.Random(7))
        occupied = board._occupied
        # Laczna liczba zajetych pol = suma dlugosci (brak nakladania).
        self.assertEqual(len(occupied), sum(game.FLEET_SIZES))

    def test_in_bounds(self):
        board = Board()
        self.assertTrue(board.in_bounds(0, 0))
        self.assertTrue(board.in_bounds(9, 9))
        self.assertFalse(board.in_bounds(10, 0))
        self.assertFalse(board.in_bounds(-1, 5))

    def test_receive_shot_miss_hit_sunk(self):
        board = Board()
        board.ships = [Ship({(0, 0), (1, 0)})]
        board._occupied = {(0, 0), (1, 0)}
        self.assertEqual(board.receive_shot(5, 5), game.RESULT_MISS)
        self.assertEqual(board.receive_shot(0, 0), game.RESULT_HIT)
        self.assertEqual(board.receive_shot(1, 0), game.RESULT_SUNK)

    def test_already_shot(self):
        board = Board()
        board.ships = [Ship({(0, 0)})]
        board._occupied = {(0, 0)}
        self.assertFalse(board.already_shot(3, 3))
        board.receive_shot(3, 3)
        self.assertTrue(board.already_shot(3, 3))

    def test_all_sunk(self):
        board = Board()
        board.ships = [Ship({(0, 0)}), Ship({(2, 2)})]
        board._occupied = {(0, 0), (2, 2)}
        self.assertFalse(board.all_sunk())
        board.receive_shot(0, 0)
        board.receive_shot(2, 2)
        self.assertTrue(board.all_sunk())

    def test_all_sunk_false_for_empty_board(self):
        board = Board()
        self.assertFalse(board.all_sunk())


if __name__ == "__main__":
    unittest.main()
