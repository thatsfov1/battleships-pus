import logging
import uuid
import time
import socket
import threading
from typing import Any
from . import protocol
from . import auth
from . import session
from . import keepalive

SERVER_VERSION: str = "1.0.0"

class ClientSession:
    def __init__(self, conn: Any, addr: tuple[str, int], session_manager: session.SessionManager):
        self.conn = conn
        self.addr = addr
        self.session_manager = session_manager
        self.authenticated = False
        self.auth_attempts = 0
        self.username = None
        self.stop_event = threading.Event()

    def _send_ack(self, msg_id: str):
        if msg_id:
            protocol.send_message(self.conn, {
                "type": "ACK",
                "msg_id": msg_id,
                "timestamp": time.time()
            })

    def handle(self):
        try:
            self.conn.settimeout(30.0)
            keepalive.start_keepalive_thread(self.conn, self.stop_event)

            msg = protocol.receive_message(self.conn)
            if msg.get("type") != "HELLO":
                logging.warning("Klient %s: oczekiwano HELLO", self.addr)
                return

            logging.info("Klient %s HELLO (wersja: %s)", self.addr, msg.get("client_version"))
            
            protocol.send_message(self.conn, {
                "type": "WELCOME",
                "msg_id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "server_version": SERVER_VERSION
            })

            while self.auth_attempts < 3:
                msg = protocol.receive_message(self.conn)
                msg_type = msg.get("type")

                if msg_type == "ERROR" and msg.get("code") == "INVALID_JSON":
                     return
                
                if msg_type == "PING":
                    protocol.send_message(self.conn, {"type": "PONG", "msg_id": str(uuid.uuid4()), "timestamp": time.time()})
                    continue

                if msg_type != "AUTH":
                    logging.warning("Klient %s: oczekiwano AUTH, otrzymano %s", self.addr, msg_type)
                    break

                username = msg.get("username")
                password_hash = msg.get("password_hash")

                if auth.verify_user(username, password_hash):
                    self.authenticated = True
                    self.username = username
                    token = auth.generate_token(username)
                    logging.info("Uzytkownik %s zalogowany (%s)", username, self.addr)
                    protocol.send_message(self.conn, {
                        "type": "AUTH_OK",
                        "msg_id": str(uuid.uuid4()),
                        "timestamp": time.time(),
                        "token": token
                    })
                    break
                else:
                    self.auth_attempts += 1
                    logging.warning("Nieudane logowanie (%d/3) dla %s od %s", self.auth_attempts, username, self.addr)
                    protocol.send_message(self.conn, {
                        "type": "AUTH_FAIL",
                        "msg_id": str(uuid.uuid4()),
                        "timestamp": time.time(),
                        "reason": "Invalid credentials"
                    })

            if not self.authenticated:
                return

            while True:
                msg = protocol.receive_message(self.conn)
                msg_type = msg.get("type")
                msg_id = msg.get("msg_id")
                
                if msg_type == "ERROR" and msg.get("code") == "INVALID_JSON":
                    break

                if msg_type == "PING":
                    protocol.send_message(self.conn, {"type": "PONG", "msg_id": str(uuid.uuid4()), "timestamp": time.time()})
                    continue

                if msg_type in ("CREATE_GAME", "JOIN_GAME", "MOVE"):
                    self._send_ack(msg_id)
                    
                    if msg_type == "CREATE_GAME":
                        sid = self.session_manager.create_game(self)
                        if sid:
                            protocol.send_message(self.conn, {
                                "type": "GAME_CREATED",
                                "msg_id": str(uuid.uuid4()),
                                "timestamp": time.time(),
                                "session_id": sid
                            })
                        else:
                            protocol.send_message(self.conn, {
                                "type": "ERROR",
                                "msg_id": str(uuid.uuid4()),
                                "timestamp": time.time(),
                                "message": "Aktywna sesja juz istnieje"
                            })
                    elif msg_type == "JOIN_GAME":
                        if not self.session_manager.join_game(self):
                            protocol.send_message(self.conn, {
                                "type": "ERROR",
                                "msg_id": str(uuid.uuid4()),
                                "timestamp": time.time(),
                                "message": "Brak wolnych gier"
                            })
                    elif msg_type == "MOVE":
                        logging.info("Ruch gracza %s: %s", self.username, msg.get("move"))

                elif msg_type is None:
                    break
                else:
                    logging.warning("Nieobsługiwany typ: %s od %s", msg_type, self.username)

        except socket.timeout:
            logging.warning("Timeout polaczenia (30s) dla %s", self.username or self.addr)
        except Exception as e:
            logging.error("Blad sesji %s: %s", self.username or self.addr, e)
        finally:
            self.stop_event.set()
            self.session_manager.remove_player_from_sessions(self)
            try:
                self.conn.close()
            except:
                pass
            logging.info("Sesja zakonczona: %s", self.username or self.addr)
