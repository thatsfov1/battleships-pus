"""Warstwa sieciowa klienta: polaczenie TLS, wysylka/odbior JSON-over-TCP,
watek odbiorczy, keep-alive (PING) oraz logowanie/reconnect.

Wiadomosci przychodzace trafiaja do kolejki `inbox`, z ktorej korzysta warstwa
rozgrywki. PING od serwera obslugiwany jest automatycznie (odpowiedz PONG).
"""

from __future__ import annotations

import json
import os
import queue
import socket
import ssl
import threading
import time
import uuid
from typing import Optional

from . import config

DISCONNECTED = "__DISCONNECTED__"
# Komunikaty kontrolne pomijane podczas oczekiwania na konkretna odpowiedz.
_CONTROL_TYPES = {"ACK", "PONG", "PING"}


class NetworkClient:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or config.HOST
        self.port = port or config.PORT
        self.sock: Optional[ssl.SSLSocket] = None
        self.reader = None
        self.inbox: "queue.Queue[dict]" = queue.Queue()
        self.token: Optional[str] = None
        self.cert_verified = False
        self._stop = threading.Event()
        self._recv_thread: Optional[threading.Thread] = None
        self._ping_thread: Optional[threading.Thread] = None
        self._send_lock = threading.Lock()

    # --- nawiazywanie polaczenia -------------------------------------------------

    def _make_context(self) -> ssl.SSLContext:
        if os.path.exists(config.CA_CERT):
            ctx = ssl.create_default_context(cafile=config.CA_CERT)
            ctx.check_hostname = True
            self.cert_verified = True
            return ctx
        self.cert_verified = False
        return ssl._create_unverified_context()

    def connect(self) -> None:
        ctx = self._make_context()
        raw = socket.create_connection((self.host, self.port), timeout=config.CONNECT_TIMEOUT)
        self.sock = ctx.wrap_socket(raw, server_hostname=config.SERVER_HOSTNAME)
        self.reader = self.sock.makefile("rb")
        self._stop.clear()
        self._drain_inbox()
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True, name="recv")
        self._recv_thread.start()

    def connect_with_retry(self, attempts: int = None, delay: int = None) -> bool:
        attempts = attempts if attempts is not None else config.RECONNECT_ATTEMPTS
        delay = delay if delay is not None else config.RECONNECT_DELAY
        for i in range(attempts):
            try:
                self.connect()
                return True
            except (OSError, ssl.SSLError):
                if i < attempts - 1:
                    time.sleep(delay)
        return False

    # --- wysylka / odbior --------------------------------------------------------

    def send(self, msg_type: str, **fields) -> str:
        msg = {"type": msg_type, "msg_id": str(uuid.uuid4()), "timestamp": time.time(), **fields}
        data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        with self._send_lock:
            if self.sock is None:
                raise ConnectionError("Brak polaczenia z serwerem.")
            self.sock.sendall(data)
        return msg["msg_id"]

    def _recv_loop(self) -> None:
        try:
            while not self._stop.is_set():
                line = self.reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if msg.get("type") == "PING":
                    try:
                        self.send("PONG")
                    except Exception:
                        break
                    continue
                self.inbox.put(msg)
        finally:
            self.inbox.put({"type": DISCONNECTED})

    def wait_for(self, types: set, timeout: float = 10.0) -> Optional[dict]:
        """Czeka na wiadomosc jednego z `types`, pomijajac komunikaty kontrolne.
        Zwraca dict albo None po uplywie czasu / rozlaczeniu."""
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return None
            try:
                msg = self.inbox.get(timeout=remaining)
            except queue.Empty:
                return None
            mtype = msg.get("type")
            if mtype == DISCONNECTED:
                return None
            if mtype in types:
                return msg
            if mtype in _CONTROL_TYPES:
                continue
            # nieoczekiwana wiadomosc spoza zestawu — pomijamy w fazie handshake

    # --- wysokopoziomowe operacje ------------------------------------------------

    def login(self, username: str, password_hash: str) -> tuple[bool, str]:
        self.send("HELLO", client_version=config.CLIENT_VERSION)
        if self.wait_for({"WELCOME"}, timeout=10) is None:
            return False, "Brak odpowiedzi WELCOME od serwera."
        self.send("AUTH", username=username, password_hash=password_hash)
        resp = self.wait_for({"AUTH_OK", "AUTH_FAIL", "ERROR"}, timeout=10)
        if resp is None:
            return False, "Brak odpowiedzi na AUTH."
        if resp.get("type") == "AUTH_OK":
            self.token = resp.get("token")
            return True, self.token or ""
        return False, resp.get("reason") or resp.get("message") or "Logowanie odrzucone."

    def start_keepalive(self) -> None:
        self._ping_thread = threading.Thread(target=self._ping_loop, daemon=True, name="ping")
        self._ping_thread.start()

    def _ping_loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(config.PING_INTERVAL)
            if self._stop.is_set():
                break
            try:
                self.send("PING")
            except Exception:
                break

    def close(self, say_bye: bool = True) -> None:
        if say_bye and self.sock is not None:
            try:
                self.send("BYE")
            except Exception:
                pass
        self._stop.set()
        try:
            if self.sock is not None:
                self.sock.close()
        except Exception:
            pass
        self.sock = None

    def _drain_inbox(self) -> None:
        try:
            while True:
                self.inbox.get_nowait()
        except queue.Empty:
            pass
