import uuid
import time
import logging
import threading
from typing import Dict, Optional, Any
from . import protocol
from . import game

class GameSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.players: list[Any] = []
        self.lock = threading.Lock()
        self.status = "LOBBY"
        self.current_turn = None
        self.boards = {}
        self.ready: set[str] = set()
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

    def opponent_of(self, username: str):
        for p in self.players:
            if p.username != username:
                return p
        return None

    def setup_boards(self) -> None:
        """Rozstawia floty obu graczy na poczatku rozgrywki."""
        self.boards = {}
        for p in self.players:
            board = game.Board()
            board.place_fleet()
            self.boards[p.username] = board

    def get_state(self, username: str) -> dict:
        own = self.boards.get(username)
        opponent = self.opponent_of(username)
        tracking = self.boards.get(opponent.username) if opponent else None
        return {
            "session_id": self.session_id,
            "current_turn": self.current_turn,
            "status": self.status,
            "your_board": own.own_view() if own else [],
            "tracking_board": tracking.tracking_view() if tracking else [],
            "history": self.history,
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
        """Po skompletowaniu graczy rozpoczyna faze rozmieszczania statkow."""
        if session.is_full() and session.status == "LOBBY":
            session.status = "PLACEMENT"
            for p in session.players:
                protocol.send_message(p.conn, {
                    "type": "PLACEMENT",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "session_id": session.session_id,
                    "players": [player.username for player in session.players],
                    "fleet": list(game.FLEET_SIZES),
                })

    def handle_placement(self, player, ships) -> Optional[str]:
        """Przyjmuje reczne rozmieszczenie floty. Gdy obaj gracze sa gotowi,
        rozpoczyna rozgrywke (GAME_START). Zwraca kod bledu lub None."""
        with self.lock:
            session = self._find_active_session(player.username)
        if session is None:
            return "SESSION_NOT_FOUND"

        started = False
        with session.lock:
            if session.status != "PLACEMENT":
                return "INVALID_PLACEMENT"
            board = game.Board()
            if not isinstance(ships, list) or not board.place_fleet_manual(ships):
                return "INVALID_PLACEMENT"
            session.boards[player.username] = board
            session.ready.add(player.username)

            if len(session.ready) >= 2:
                session.status = "IN_PROGRESS"
                session.current_turn = session.players[0].username
                started = True
                recipients = list(session.players)
                session_id = session.session_id
                current_turn = session.current_turn
                players = [p.username for p in session.players]
                own_views = {p.username: session.boards[p.username].own_view() for p in session.players}

        if started:
            for p in recipients:
                protocol.send_message(p.conn, {
                    "type": "GAME_START",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "session_id": session_id,
                    "players": players,
                    "current_turn": current_turn,
                    "your_board": own_views[p.username],
                })
        return None

    def handle_move(self, player, x: int, y: int) -> Optional[str]:
        """Przetwarza ruch gracza. Zwraca kod bledu lub None przy sukcesie.

        Przy powodzeniu rozsyla MOVE_RESULT do obu graczy, a po zatopieniu
        ostatniego statku rowniez GAME_END i usuwa sesje.
        """
        with self.lock:
            session = self._find_active_session(player.username)
        if session is None:
            return "SESSION_NOT_FOUND"

        finished_winner = None
        with session.lock:
            if session.status != "IN_PROGRESS":
                return "SESSION_NOT_FOUND"
            if session.current_turn != player.username:
                return "NOT_YOUR_TURN"

            opponent = session.opponent_of(player.username)
            if opponent is None:
                return "SESSION_NOT_FOUND"

            target = session.boards.get(opponent.username)
            if target is None or not target.in_bounds(x, y) or target.already_shot(x, y):
                return "INVALID_MOVE"

            result = target.receive_shot(x, y)
            sunk_len = target.last_sunk_len if result == "SUNK" else 0
            session.history.append({"by": player.username, "x": x, "y": y, "result": result})

            if target.all_sunk():
                session.status = "FINISHED"
                finished_winner = player.username
                next_turn = None
            else:
                session.current_turn = opponent.username
                next_turn = session.current_turn

            move_result = {
                "type": "MOVE_RESULT",
                "msg_id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "x": x,
                "y": y,
                "result": result,
                "sunk_len": sunk_len,
                "by": player.username,
                "next_turn": next_turn,
            }
            recipients = list(session.players)

        for p in recipients:
            try:
                protocol.send_message(p.conn, move_result)
            except Exception:
                pass

        if finished_winner is not None:
            self._broadcast_game_end(session, recipients, "VICTORY", finished_winner)
        return None

    def _find_active_session(self, username: str) -> Optional[GameSession]:
        for session in self.sessions.values():
            if session.status != "FINISHED" and any(p.username == username for p in session.players):
                return session
        return None

    def _broadcast_game_end(self, session, recipients, reason, winner):
        end_msg = {
            "type": "GAME_END",
            "msg_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "reason": reason,
            "winner": winner,
        }
        for p in recipients:
            try:
                protocol.send_message(p.conn, end_msg)
            except Exception:
                pass
        with self.lock:
            self.sessions.pop(session.session_id, None)

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

    def force_terminate_session(self, session_id, reason, loser_username=None):
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                winner = None
                if loser_username is not None:
                    opp = session.opponent_of(loser_username)
                    winner = opp.username if opp else None
                for p in session.players:
                    try:
                        protocol.send_message(p.conn, {
                            "type": "GAME_END",
                            "msg_id": str(uuid.uuid4()),
                            "timestamp": time.time(),
                            "reason": reason,
                            "winner": winner,
                        })
                    except:
                        pass
                del self.sessions[session_id]
