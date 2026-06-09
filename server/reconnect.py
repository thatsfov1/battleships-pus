import time
import threading
import logging
import uuid
from typing import Dict, Optional, Any
from . import protocol

class ReconnectManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.disconnected_players: Dict[str, dict] = {}
        self.reconnect_timeout = 60
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self._start_cleanup_thread()

    def player_disconnected(self, username: str, session_id: str):
        with self.lock:
            self.disconnected_players[username] = {
                "session_id": session_id,
                "timestamp": time.time()
            }
            logging.info(f"Gracz {username} rozlaczony. Oczekiwanie na reconnect (60s).")

    def try_reconnect(self, username: str) -> Optional[str]:
        with self.lock:
            if username in self.disconnected_players:
                data = self.disconnected_players.pop(username)
                logging.info(f"Gracz {username} polaczyl sie ponownie.")
                return data["session_id"]
        return None

    def _start_cleanup_thread(self):
        t = threading.Thread(target=self._cleanup_loop, daemon=True, name="ReconnectCleanup")
        t.start()

    def _cleanup_loop(self):
        while not self.stop_event.is_set():
            time.sleep(1)
            now = time.time()
            to_terminate = []
            with self.lock:
                users_to_remove = []
                for user, data in self.disconnected_players.items():
                    if now - data["timestamp"] > self.reconnect_timeout:
                        to_terminate.append((data["session_id"], user))
                        users_to_remove.append(user)
                for user in users_to_remove:
                    del self.disconnected_players[user]

            for sid, loser in to_terminate:
                self.session_manager.force_terminate_session(sid, "DISCONNECT", loser)
