"""Warstwa protokolu JSON-over-TCP dla serwera gry."""

from __future__ import annotations

import json
import time
from typing import Any, Final

DELIMITER: Final[bytes] = b"\n"
ENCODING: Final[str] = "utf-8"
REQUIRED_FIELDS: Final[set[str]] = {"type", "msg_id", "timestamp"}
MESSAGE_ID_TTL_SECONDS: Final[int] = 60

INVALID_JSON: Final[str] = "INVALID_JSON"
INVALID_TYPE: Final[str] = "INVALID_TYPE"
DUPLICATE_MESSAGE: Final[str] = "DUPLICATE_MESSAGE"

_recent_message_ids: dict[Any, float] = {}


def send_message(conn: Any, msg_dict: dict[str, Any]) -> None:
    """Serializuje slownik do JSON i wysyla go przez socket z delimiterem LF"""
    payload = json.dumps(msg_dict, ensure_ascii=False).encode(ENCODING) + DELIMITER
    conn.sendall(payload)


def receive_message(conn: Any) -> dict[str, Any]:
    """Odbiera jedna wiadomosc JSON zakonczona LF i zwraca zdeserializowany slownik"""
    raw_message = _recv_until_delimiter(conn)
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


def _recv_until_delimiter(conn: Any) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = conn.recv(1)
        if chunk == b"":
            break
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
