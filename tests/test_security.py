import unittest
import time
from server.security import SecurityManager

class TestSecurity(unittest.TestCase):
    def test_rate_limiting(self):
        sm = SecurityManager()
        addr = "127.0.0.1"
        for _ in range(20):
            self.assertFalse(sm.is_rate_limited(addr))
        self.assertTrue(sm.is_rate_limited(addr))

    def test_replay_protection(self):
        sm = SecurityManager()
        self.assertTrue(sm.is_replay_attack(time.time() - 31))
        self.assertFalse(sm.is_replay_attack(time.time()))

if __name__ == "__main__":
    unittest.main()
