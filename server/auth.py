import sqlite3
import jwt
import datetime
from typing import Optional

DB_PATH = "users.db"
SECRET_KEY = "super_tajny_klucz_serwera" # W produkcji powinno byc w .env
ALGORITHM = "HS256"

def verify_user(username: str, password_hash: str) -> bool:
    """Weryfikuje uzytkownika porownujac hashe bezposrednio."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def generate_token(username: str) -> str:
    """Generuje token JWT wazny przez 1 godzine."""
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Dekoduje token JWT."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
