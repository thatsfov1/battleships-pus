import time
import threading
from typing import Dict, List

class SecurityManager:
    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        self.max_messages = 20
        self.window_seconds = 10
        self.timestamp_window = 30

    def is_rate_limited(self, addr: str) -> bool:
        now = time.time()
        with self.lock:
            if addr not in self.rate_limits:
                self.rate_limits[addr] = [now]
                return False
            
            self.rate_limits[addr] = [t for t in self.rate_limits[addr] if now - t < self.window_seconds]
            if len(self.rate_limits[addr]) >= self.max_messages:
                return True
            
            self.rate_limits[addr].append(now)
            return False

    def is_replay_attack(self, msg_timestamp: float) -> bool:
        return abs(time.time() - msg_timestamp) > self.timestamp_window
