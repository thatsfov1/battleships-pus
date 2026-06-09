import unittest

from client import game_ui
from client.main import GameClient, EMPTY


class TestParseCoords(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(game_ui.parse_coords("A1"), (0, 0))
        self.assertEqual(game_ui.parse_coords("B5"), (1, 4))
        self.assertEqual(game_ui.parse_coords("J10"), (9, 9))

    def test_case_and_spaces(self):
        self.assertEqual(game_ui.parse_coords("c 7"), (2, 6))
        self.assertEqual(game_ui.parse_coords("d,3"), (3, 2))

    def test_invalid(self):
        self.assertIsNone(game_ui.parse_coords(""))
        self.assertIsNone(game_ui.parse_coords("Z1"))
        self.assertIsNone(game_ui.parse_coords("A0"))
        self.assertIsNone(game_ui.parse_coords("A11"))
        self.assertIsNone(game_ui.parse_coords("5"))

    def test_coord_label_roundtrip(self):
        for x in range(10):
            for y in range(10):
                self.assertEqual(game_ui.parse_coords(game_ui.coord_label(x, y)), (x, y))


class TestRender(unittest.TestCase):
    def test_render_board_has_header_and_rows(self):
        out = game_ui.render_board(EMPTY(), "T")
        lines = out.splitlines()
        self.assertEqual(lines[0], "T")
        self.assertIn("A B C D E F G H I J", lines[1])
        self.assertEqual(len(lines), 12)  # tytul + naglowek + 10 wierszy

    def test_symbols(self):
        grid = EMPTY()
        grid[0][0] = "S"
        grid[1][1] = "X"
        grid[2][2] = "o"
        out = game_ui.render_board(grid, "T")
        self.assertIn("#", out)
        self.assertIn("X", out)
        self.assertIn("o", out)


class TestClientStateLogic(unittest.TestCase):
    def _client(self):
        gc = GameClient("localhost", 5000)
        gc.username = "me"
        gc.tracking = EMPTY()
        gc.own = EMPTY()
        return gc

    def test_my_hit_marks_tracking(self):
        gc = self._client()
        gc._apply_move_result({"x": 3, "y": 4, "result": "HIT", "by": "me", "next_turn": "opp"})
        self.assertEqual(gc.tracking[4][3], "X")
        self.assertEqual(gc.current_turn, "opp")

    def test_my_miss_marks_tracking(self):
        gc = self._client()
        gc._apply_move_result({"x": 0, "y": 0, "result": "MISS", "by": "me", "next_turn": "opp"})
        self.assertEqual(gc.tracking[0][0], "o")

    def test_opponent_hit_marks_own(self):
        gc = self._client()
        gc._apply_move_result({"x": 2, "y": 5, "result": "SUNK", "by": "opp", "next_turn": "me"})
        self.assertEqual(gc.own[5][2], "X")
        self.assertEqual(gc.current_turn, "me")

    def test_game_end_sets_over(self):
        gc = self._client()
        gc._apply_game_end({"winner": "me", "reason": "VICTORY"})
        self.assertTrue(gc.over)


if __name__ == "__main__":
    unittest.main()
