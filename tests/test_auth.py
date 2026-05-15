import unittest
import hashlib
import os
import sqlite3
from server import auth

class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Upewnij sie ze baza istnieje i ma dane
        if not os.path.exists("users.db"):
            import init_db
            init_db.init_db()

    def test_verify_valid_user(self):
        username = "user1"
        password_hash = hashlib.sha256(b"pass1").hexdigest()
        self.assertTrue(auth.verify_user(username, password_hash))

    def test_verify_invalid_password(self):
        username = "user1"
        password_hash = hashlib.sha256(b"wrong").hexdigest()
        self.assertFalse(auth.verify_user(username, password_hash))

    def test_verify_nonexistent_user(self):
        username = "nobody"
        password_hash = hashlib.sha256(b"pass1").hexdigest()
        self.assertFalse(auth.verify_user(username, password_hash))

    def test_token_generation_and_decoding(self):
        username = "user1"
        token = auth.generate_token(username)
        self.assertIsNotNone(token)
        
        decoded = auth.decode_token(token)
        self.assertEqual(decoded["sub"], username)

    def test_invalid_token(self):
        self.assertIsNone(auth.decode_token("invalid.token.here"))

if __name__ == "__main__":
    unittest.main()
