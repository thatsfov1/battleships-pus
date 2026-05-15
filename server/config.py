import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 5000))
JWT_SECRET = os.getenv("JWT_SECRET", "super_tajny_klucz_serwera")
DB_PATH = os.getenv("DB_PATH", "users.db")
CERT_PATH = os.getenv("CERT_PATH", "certs/server.crt")
KEY_PATH = os.getenv("KEY_PATH", "certs/server.key")
LOG_PATH = os.getenv("LOG_PATH", "logs/server.log")
RECONNECT_TIMEOUT = int(os.getenv("RECONNECT_TIMEOUT", 60))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", 20))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 10))
MESSAGE_SIZE_LIMIT = int(os.getenv("MESSAGE_SIZE_LIMIT", 8192))
