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
        self.status = "LOBBY"
        self.current_turn = None
        self.boards = {}
        self.history = []

    def is_full(self) -> bool:
        return len(self.players) >= 2

    def add_player(self, player) -> bool:
        with self.lock:
            if self.is_full():
                return False
            self.players.append(player)
            if self.is_full():
                self.current_turn = self.players[0].username
            return True

    def get_state(self, username: str) -> dict:
        return {
            "session_id": self.session_id,
            "current_turn": self.current_turn,
            "board": self.boards.get(username, []),
            "history": self.history,
            "status": self.status
        }

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.lock = threading.Lock()
        from .reconnect import ReconnectManager
        self.reconnect_manager = ReconnectManager(self)

    def create_game(self, player) -> Optional[str]:
        with self.lock:
            for session in self.sessions.values():
                if any(p.username == player.username for p in session.players) and session.status != "FINISHED":
                    return None
            
            session_id = str(uuid.uuid4())
            new_session = GameSession(session_id)
            new_session.add_player(player)
            self.sessions[session_id] = new_session
            return session_id

    def join_game(self, player) -> Optional[str]:
        with self.lock:
            reconnected_sid = self.reconnect_manager.try_reconnect(player.username)
            if reconnected_sid:
                session = self.sessions.get(reconnected_sid)
                if session:
                    with session.lock:
                        for i, p in enumerate(session.players):
                            if p.username == player.username:
                                session.players[i] = player
                                break
                    self.send_game_state(player, session)
                    return reconnected_sid

            for session in self.sessions.values():
                if any(p.username == player.username for p in session.players) and session.status != "FINISHED":
                    return None

            for session in self.sessions.values():
                if not session.is_full() and session.status == "LOBBY":
                    if session.add_player(player):
                        self._check_start_game(session)
                        return session.session_id
            return None

    def send_game_state(self, player, session):
        protocol.send_message(player.conn, {
            "type": "GAME_STATE",
            "msg_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            **session.get_state(player.username)
        })

    def _check_start_game(self, session: GameSession):
        if session.is_full() and session.status == "LOBBY":
            session.status = "IN_PROGRESS"
            for p in session.players:
                protocol.send_message(p.conn, {
                    "type": "GAME_START",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "session_id": session.session_id,
                    "players": [player.username for player in session.players]
                })

    def remove_player_from_sessions(self, player):
        with self.lock:
            for session_id, session in list(self.sessions.items()):
                if player in session.players:
                    if session.status == "IN_PROGRESS":
                        self.reconnect_manager.player_disconnected(player.username, session_id)
                    else:
                        with session.lock:
                            if player in session.players:
                                session.players.remove(player)
                            if not session.players:
                                if session_id in self.sessions:
                                    del self.sessions[session_id]

    def force_terminate_session(self, session_id, reason):
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                for p in session.players:
                    try:
                        protocol.send_message(p.conn, {
                            "type": "GAME_END",
                            "msg_id": str(uuid.uuid4()),
                            "timestamp": time.time(),
                            "reason": reason
                        })
                    except:
                        pass
                del self.sessions[session_id]
