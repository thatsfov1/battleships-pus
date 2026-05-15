import uuid
import time
import logging
import threading
from typing import Dict, Optional, Any
from . import protocol

class GameSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.players: list[Any] = []
        self.lock = threading.Lock()
        self.status = "LOBBY" # LOBBY, IN_PROGRESS, FINISHED

    def is_full(self) -> bool:
        return len(self.players) >= 2

    def add_player(self, player) -> bool:
        with self.lock:
            if self.is_full():
                return False
            self.players.append(player)
            return True

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.lock = threading.Lock()

    def create_game(self, player) -> Optional[str]:
        """Tworzy nowe lobby dla gracza."""
        with self.lock:
            for session in self.sessions.values():
                if player in session.players and session.status != "FINISHED":
                    return None
            
            session_id = str(uuid.uuid4())
            new_session = GameSession(session_id)
            new_session.add_player(player)
            self.sessions[session_id] = new_session
            logging.info("Utworzono nowa sesje gry: %s przez %s", session_id, player.username)
            return session_id

    def join_game(self, player) -> Optional[str]:
        """Przypisuje gracza do pierwszego wolnego lobby."""
        with self.lock:
            for session in self.sessions.values():
                if player in session.players and session.status != "FINISHED":
                    return None

            for session in self.sessions.values():
                if not session.is_full() and session.status == "LOBBY":
                    if session.add_player(player):
                        logging.info("Gracz %s dolaczyl do sesji %s", player.username, session.session_id)
                        self._check_start_game(session)
                        return session.session_id
            return None

    def get_session(self, session_id: str) -> Optional[GameSession]:
        with self.lock:
            return self.sessions.get(session_id)

    def _check_start_game(self, session: GameSession):
        if session.is_full() and session.status == "LOBBY":
            session.status = "IN_PROGRESS"
            logging.info("Start gry w sesji %s", session.session_id)
            for p in session.players:
                protocol.send_message(p.conn, {
                    "type": "GAME_START",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "session_id": session.session_id,
                    "players": [player.username for player in session.players]
                })

    def remove_player_from_sessions(self, player):
        """Usuwa gracza ze wszystkich aktywnych sesji (np. po rozlaczeniu)."""
        with self.lock:
            for session_id, session in list(self.sessions.items()):
                if player in session.players:
                    with session.lock:
                        session.players.remove(player)
                        if not session.players:
                            del self.sessions[session_id]
                            logging.info("Usunieto pusta sesje %s", session_id)
                        else:
                            session.status = "LOBBY"
