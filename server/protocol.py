"""Warstwa protokolu JSON-over-TCP dla serwera gry."""

from __future__ import annotations

import json
import threading
import time
import weakref
from typing import Any, Final, Optional

DELIMITER: Final[bytes] = b"\n"
ENCODING: Final[str] = "utf-8"
REQUIRED_FIELDS: Final[set[str]] = {"type", "msg_id", "timestamp"}
MESSAGE_ID_TTL_SECONDS: Final[int] = 60
MAX_MESSAGE_SIZE: Final[int] = 8192

INVALID_JSON: Final[str] = "INVALID_JSON"
INVALID_TYPE: Final[str] = "INVALID_TYPE"
DUPLICATE_MESSAGE: Final[str] = "DUPLICATE_MESSAGE"
MESSAGE_TOO_LARGE: Final[str] = "MESSAGE_TOO_LARGE"

_recent_message_ids: dict[Any, float] = {}

# Lock zapisu per-polaczenie. Do jednego conn pisze wiele watkow (handler,
# keepalive, broadcasty innych graczy) — rownoczesne sendall na obiekcie SSL
# korumpuje rekordy TLS. Serializujemy zapisy bez serializowania odczytu.
_send_locks: "weakref.WeakKeyDictionary[Any, threading.Lock]" = weakref.WeakKeyDictionary()
_send_locks_guard = threading.Lock()


def _send_lock_for(conn: Any) -> threading.Lock:
    with _send_locks_guard:
        lock = _send_locks.get(conn)
        if lock is None:
            lock = threading.Lock()
            _send_locks[conn] = lock
        return lock


def send_message(conn: Any, msg_dict: dict[str, Any]) -> None:
    payload = json.dumps(msg_dict, ensure_ascii=False).encode(ENCODING) + DELIMITER
    try:
        lock = _send_lock_for(conn)
    except TypeError:
        # obiekt nie obsluguje weakref (np. niektore mocki w testach)
        conn.sendall(payload)
        return
    with lock:
        conn.sendall(payload)


def receive_message(conn: Any) -> dict[str, Any]:
    raw_message = _recv_until_delimiter(conn)
    if raw_message is None:
        return _error(MESSAGE_TOO_LARGE)
    
    try:
        message = json.loads(raw_message.decode(ENCODING))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(INVALID_JSON)

    if not isinstance(message, dict):
        return _error(INVALID_TYPE)

    missing_fields = REQUIRED_FIELDS - message.keys()
    if missing_fields:
        return _error(INVALID_TYPE)

    if _is_duplicate_message(message["msg_id"]):
        return _error(DUPLICATE_MESSAGE)

    return message


def _recv_until_delimiter(conn: Any) -> Optional[bytes]:
    chunks: list[bytes] = []
    total_size = 0
    while True:
        try:
            chunk = conn.recv(1)
        except Exception:
            break
            
        if chunk == b"":
            break
            
        total_size += len(chunk)
        if total_size > MAX_MESSAGE_SIZE:
            return None
            
        if chunk == DELIMITER:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _is_duplicate_message(msg_id: Any) -> bool:
    now = time.time()
    _remove_expired_message_ids(now)

    if msg_id in _recent_message_ids:
        return True

    _recent_message_ids[msg_id] = now
    return False


def _remove_expired_message_ids(now: float) -> None:
    expired_ids = [
        msg_id
        for msg_id, seen_at in _recent_message_ids.items()
        if now - seen_at > MESSAGE_ID_TTL_SECONDS
    ]
    for msg_id in expired_ids:
        del _recent_message_ids[msg_id]


def _error(code: str) -> dict[str, str]:
    return {"type": "ERROR", "code": code}
