import unittest
import time
import threading
from server.session import SessionManager, GameSession

class MockPlayer:
    def __init__(self, username):
        self.username = username
        self.conn = self

    def sendall(self, data):
        pass

class TestReconnect(unittest.TestCase):
    def test_reconnect_within_timeout(self):
        sm = SessionManager()
        p1 = MockPlayer("user1")
        sid = sm.create_game(p1)
        
        p2 = MockPlayer("user2")
        sm.join_game(p2) # Start game
        
        session = sm.sessions[sid]
        self.assertEqual(session.status, "IN_PROGRESS")
        
        sm.remove_player_from_sessions(p1)
        self.assertIn("user1", sm.reconnect_manager.disconnected_players)
        
        p1_new = MockPlayer("user1")
        sm.join_game(p1_new)
        
        self.assertNotIn("user1", sm.reconnect_manager.disconnected_players)
        self.assertEqual(session.players[0], p1_new)

    def test_reconnect_after_timeout(self):
        sm = SessionManager()
        sm.reconnect_manager.reconnect_timeout = 0.1
        
        p1 = MockPlayer("user1")
        sid = sm.create_game(p1)
        p2 = MockPlayer("user2")
        sm.join_game(p2)
        
        sm.remove_player_from_sessions(p1)
        # Give cleanup thread more time to run (sleep 1s for 0.1s timeout)
        time.sleep(1.5)
        
        self.assertNotIn(sid, sm.sessions)

if __name__ == "__main__":
    unittest.main()
