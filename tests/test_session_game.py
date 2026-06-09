import json
import unittest

from server.session import SessionManager
from server.game import Board, Ship


class CapturingConn:
    def __init__(self):
        self.messages = []

    def sendall(self, data):
        self.messages.append(json.loads(data.decode("utf-8").strip()))


class MockPlayer:
    def __init__(self, username):
        self.username = username
        self.conn = CapturingConn()

    def types(self):
        return [m["type"] for m in self.conn.messages]


def valid_fleet():
    # zgodne z FLEET_SIZES (4,3,3,3,2)
    return [
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 4), (1, 4), (2, 4)],
        [(0, 6), (1, 6), (2, 6)],
        [(0, 8), (1, 8)],
    ]


class TestSessionGame(unittest.TestCase):
    def _start_game(self):
        sm = SessionManager()
        p1 = MockPlayer("user1")
        sid = sm.create_game(p1)
        p2 = MockPlayer("user2")
        sm.join_game(p2)
        sm.handle_placement(p1, valid_fleet())
        sm.handle_placement(p2, valid_fleet())
        session = sm.sessions[sid]
        return sm, p1, p2, session

    def test_placement_phase_then_start(self):
        sm = SessionManager()
        p1 = MockPlayer("user1")
        sid = sm.create_game(p1)
        p2 = MockPlayer("user2")
        sm.join_game(p2)
        session = sm.sessions[sid]
        self.assertEqual(session.status, "PLACEMENT")
        self.assertIn("PLACEMENT", p1.types())

        self.assertIsNone(sm.handle_placement(p1, valid_fleet()))
        self.assertEqual(session.status, "PLACEMENT")  # czeka na drugiego
        self.assertIsNone(sm.handle_placement(p2, valid_fleet()))
        self.assertEqual(session.status, "IN_PROGRESS")
        self.assertIn("GAME_START", p2.types())

    def test_invalid_placement_rejected(self):
        sm = SessionManager()
        p1 = MockPlayer("user1")
        sm.create_game(p1)
        p2 = MockPlayer("user2")
        sm.join_game(p2)
        bad = valid_fleet()
        bad[1] = [(0, 1), (1, 1), (2, 1)]  # przylega do 4-masztowca
        self.assertEqual(sm.handle_placement(p1, bad), "INVALID_PLACEMENT")

    def test_game_start_sends_boards(self):
        sm, p1, p2, session = self._start_game()
        self.assertEqual(session.status, "IN_PROGRESS")
        self.assertIn("GAME_START", p1.types())
        self.assertIn("GAME_START", p2.types())
        self.assertEqual(session.current_turn, "user1")

    def test_move_out_of_turn_rejected(self):
        sm, p1, p2, session = self._start_game()
        self.assertEqual(sm.handle_move(p2, 0, 0), "NOT_YOUR_TURN")

    def test_invalid_move_out_of_bounds(self):
        sm, p1, p2, session = self._start_game()
        self.assertEqual(sm.handle_move(p1, 99, 99), "INVALID_MOVE")

    def test_valid_move_broadcasts_and_switches_turn(self):
        sm, p1, p2, session = self._start_game()
        target = Board()
        target.ships = [Ship({(5, 5), (5, 6)})]
        target._occupied = {(5, 5), (5, 6)}
        session.boards["user2"] = target

        self.assertIsNone(sm.handle_move(p1, 0, 0))  # pudlo
        self.assertEqual(session.current_turn, "user2")
        self.assertIn("MOVE_RESULT", p1.types())
        self.assertIn("MOVE_RESULT", p2.types())

    def test_already_shot_field_rejected(self):
        sm, p1, p2, session = self._start_game()
        target = Board()
        target.ships = [Ship({(5, 5), (5, 6)})]
        target._occupied = {(5, 5), (5, 6)}
        session.boards["user2"] = target

        sm.handle_move(p1, 0, 0)
        session.current_turn = "user1"  # wymus ponowna ture na tym samym graczu
        self.assertEqual(sm.handle_move(p1, 0, 0), "INVALID_MOVE")

    def test_sinking_last_ship_ends_game(self):
        sm, p1, p2, session = self._start_game()
        target = Board()
        target.ships = [Ship({(0, 0)})]
        target._occupied = {(0, 0)}
        session.boards["user2"] = target

        self.assertIsNone(sm.handle_move(p1, 0, 0))
        self.assertIn("GAME_END", p1.types())
        self.assertIn("GAME_END", p2.types())
        end = [m for m in p1.conn.messages if m["type"] == "GAME_END"][0]
        self.assertEqual(end["winner"], "user1")
        self.assertNotIn(session.session_id, sm.sessions)

    def test_move_without_session_returns_not_found(self):
        sm = SessionManager()
        stray = MockPlayer("ghost")
        self.assertEqual(sm.handle_move(stray, 0, 0), "SESSION_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
