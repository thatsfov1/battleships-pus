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
from .security import SecurityManager

SERVER_VERSION: str = "1.0.0"

class ClientSession:
    def __init__(self, conn: Any, addr: tuple[str, int], session_manager: session.SessionManager, security_manager: SecurityManager):
        self.conn = conn
        self.addr = addr
        self.session_manager = session_manager
        self.security_manager = security_manager
        self.authenticated = False
        self.auth_attempts = 0
        self.invalid_json_attempts = 0
        self.username = None
        self.stop_event = threading.Event()

    def _send_ack(self, msg_id: str):
        if msg_id:
            protocol.send_message(self.conn, {
                "type": "ACK",
                "msg_id": msg_id,
                "timestamp": time.time()
            })

    def _send_error(self, code: str, message: str):
        protocol.send_message(self.conn, {
            "type": "ERROR",
            "msg_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "code": code,
            "message": message,
        })

    @staticmethod
    def _extract_coords(msg: dict):
        """Wyciaga (x, y) z komunikatu MOVE. Obsluguje pola plaskie oraz
        zagniezdzone w 'move'/'payload'. Zwraca None gdy brak/niepoprawne."""
        source = msg
        for key in ("move", "payload"):
            if isinstance(msg.get(key), dict):
                source = msg[key]
                break
        x, y = source.get("x"), source.get("y")
        if isinstance(x, bool) or isinstance(y, bool):
            return None
        if isinstance(x, int) and isinstance(y, int):
            return x, y
        return None

    _MOVE_ERROR_MESSAGES = {
        "SESSION_NOT_FOUND": "Nie znaleziono aktywnej sesji.",
        "NOT_YOUR_TURN": "Nie mozesz wykonac ruchu w tej turze.",
        "INVALID_MOVE": "Niepoprawny ruch.",
    }

    def handle(self):
        try:
            self.conn.settimeout(30.0)
            keepalive.start_keepalive_thread(self.conn, self.stop_event)

            while True:
                msg = protocol.receive_message(self.conn)
                msg_type = msg.get("type")
                msg_id = msg.get("msg_id")
                msg_ts = msg.get("timestamp")

                if msg_type == "ERROR":
                    code = msg.get("code")
                    if code == "MESSAGE_TOO_LARGE":
                        logging.warning(f"Oversized message from {self.addr}")
                        return
                    if code == "INVALID_JSON":
                        self.invalid_json_attempts += 1
                        if self.invalid_json_attempts >= 5:
                            logging.warning(f"JSON spam from {self.addr}")
                            return
                        continue

                if msg_ts and self.security_manager.is_replay_attack(msg_ts):
                    protocol.send_message(self.conn, {"type": "ERROR", "code": "INVALID_TIMESTAMP"})
                    continue

                if self.security_manager.is_rate_limited(self.addr[0]):
                    protocol.send_message(self.conn, {"type": "ERROR", "code": "RATE_LIMIT"})
                    return

                if msg_type == "BYE":
                    logging.info(f"BYE od {self.addr} ({self.username})")
                    break

                if not self.authenticated:
                    if msg_type == "HELLO":
                        protocol.send_message(self.conn, {
                            "type": "WELCOME",
                            "msg_id": str(uuid.uuid4()),
                            "timestamp": time.time(),
                            "server_version": SERVER_VERSION
                        })
                    elif msg_type == "AUTH":
                        if self.auth_attempts >= 3:
                            return
                        
                        username = msg.get("username")
                        password_hash = msg.get("password_hash")

                        if auth.verify_user(username, password_hash):
                            self.authenticated = True
                            self.username = username
                            token = auth.generate_token(username)
                            protocol.send_message(self.conn, {
                                "type": "AUTH_OK",
                                "msg_id": str(uuid.uuid4()),
                                "timestamp": time.time(),
                                "token": token
                            })
                        else:
                            self.auth_attempts += 1
                            protocol.send_message(self.conn, {"type": "AUTH_FAIL", "reason": "Invalid credentials"})
                    elif msg_type == "PING":
                         protocol.send_message(self.conn, {"type": "PONG", "msg_id": str(uuid.uuid4()), "timestamp": time.time()})
                    elif msg_type is None:
                        break
                else:
                    if msg_type == "PING":
                        protocol.send_message(self.conn, {"type": "PONG", "msg_id": str(uuid.uuid4()), "timestamp": time.time()})
                    elif msg_type in ("CREATE_GAME", "JOIN_GAME", "MOVE"):
                        self._send_ack(msg_id)
                        if msg_type == "CREATE_GAME":
                            sid = self.session_manager.create_game(self)
                            if sid:
                                protocol.send_message(self.conn, {"type": "GAME_CREATED", "session_id": sid})
                            else:
                                protocol.send_message(self.conn, {"type": "ERROR", "message": "Session already exists"})
                        elif msg_type == "JOIN_GAME":
                            if not self.session_manager.join_game(self):
                                protocol.send_message(self.conn, {"type": "ERROR", "message": "No games found"})
                        elif msg_type == "MOVE":
                            coords = self._extract_coords(msg)
                            if coords is None:
                                self._send_error("INVALID_MOVE", "Brak lub niepoprawne wspolrzedne ruchu.")
                            else:
                                error = self.session_manager.handle_move(self, coords[0], coords[1])
                                if error:
                                    self._send_error(error, self._MOVE_ERROR_MESSAGES.get(error, "Blad ruchu."))
                    elif msg_type is None:
                        break

        except socket.timeout:
            logging.warning(f"Timeout {self.addr}")
        except Exception as e:
            logging.error(f"Error {self.addr}: {e}")
        finally:
            self.stop_event.set()
            self.session_manager.remove_player_from_sessions(self)
            try:
                self.conn.close()
            except:
                pass
