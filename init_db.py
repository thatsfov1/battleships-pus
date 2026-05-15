import sqlite3
import hashlib
import os

DB_PATH = "users.db"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    users = [
        ("user1", hashlib.sha256(b"pass1").hexdigest()),
        ("user2", hashlib.sha256(b"pass2").hexdigest())
    ]
    
    cursor.executemany('INSERT INTO users (username, password_hash) VALUES (?, ?)', users)
    
    conn.commit()
    conn.close()
    print(f"Baza danych {DB_PATH} została zainicjowana z testowymi użytkownikami.")

if __name__ == "__main__":
    init_db()
