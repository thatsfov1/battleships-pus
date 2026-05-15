import logging
import uuid
import time
from typing import Any
from . import protocol
from . import auth

SERVER_VERSION: str = "1.0.0"

class ClientSession:
    def __init__(self, conn: Any, addr: tuple[str, int]):
        self.conn = conn
        self.addr = addr
        self.authenticated = False
        self.auth_attempts = 0
        self.username = None

    def handle(self):
        try:
            # 1. HELLO Sequence
            msg = protocol.receive_message(self.conn)
            if msg.get("type") != "HELLO":
                logging.warning("Klient %s nie wyslal HELLO jako pierwszej wiadomosci", self.addr)
                return

            client_version = msg.get("client_version")
            logging.info("Klient %s HELLO (version: %s)", self.addr, client_version)
            
            protocol.send_message(self.conn, {
                "type": "WELCOME",
                "msg_id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "server_version": SERVER_VERSION
            })

            # 2. AUTH Sequence
            while self.auth_attempts < 3:
                msg = protocol.receive_message(self.conn)
                if msg.get("type") == "ERROR" and msg.get("code") == "INVALID_JSON":
                     # Protocol error or disconnect
                     return
                
                if msg.get("type") != "AUTH":
                    logging.warning("Klient %s wyslal %s zamiast AUTH", self.addr, msg.get("type"))
                    break

                username = msg.get("username")
                password_hash = msg.get("password_hash")

                if auth.verify_user(username, password_hash):
                    self.authenticated = True
                    self.username = username
                    token = auth.generate_token(username)
                    logging.info("Uzytkownik %s uwierzytelniony pomyslnie (%s)", username, self.addr)
                    protocol.send_message(self.conn, {
                        "type": "AUTH_OK",
                        "msg_id": str(uuid.uuid4()),
                        "timestamp": time.time(),
                        "token": token
                    })
                    break
                else:
                    self.auth_attempts += 1
                    logging.warning("Nieudana proba AUTH (%d/3) dla %s od %s", self.auth_attempts, username, self.addr)
                    protocol.send_message(self.conn, {
                        "type": "AUTH_FAIL",
                        "msg_id": str(uuid.uuid4()),
                        "timestamp": time.time(),
                        "reason": "Invalid credentials"
                    })

            if not self.authenticated:
                logging.info("Rozlaczanie %s po zbyt wielu nieudanych probach AUTH", self.addr)
                return

            # Main loop after authentication (placeholder)
            logging.info("Sesja klienta %s aktywna.", self.username)
            # while True: ...

        except Exception as e:
            logging.error("Blad sesji klienta %s: %s", self.addr, e)
        finally:
            logging.info("Zamkniecie sesji dla %s", self.addr)
