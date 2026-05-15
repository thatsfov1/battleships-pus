"""Serwer TCP gry Statki — szkielet nasłuchiwania i akceptacji połączeń."""

from __future__ import annotations

import errno
import logging
import os
import socket
import ssl
import sys
import threading
from typing import Final
from .session import SessionManager
from .handlers import ClientSession

HOST: Final[str] = ""  # wszystkie interfejsy
DEFAULT_PORT: Final[int] = 5000
BACKLOG: Final[int] = 5

CERT_FILE: Final[str] = "certs/server.crt"
KEY_FILE: Final[str] = "certs/server.key"


def listening_port() -> int:
    return int(os.environ.get("STATKI_PORT", str(DEFAULT_PORT)))


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    try:
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    except FileNotFoundError as exc:
        logging.error("Nie znaleziono plików certyfikatów: %s", exc)
        logging.error("Uruchom certs/generate_certs.sh przed startem serwera.")
        raise SystemExit(1) from exc
    return context


def handle_client(raw_conn, addr, ssl_context, session_manager):
    try:
        conn = ssl_context.wrap_socket(raw_conn, server_side=True)
        session = ClientSession(conn, addr, session_manager)
        session.handle()
    except ssl.SSLError as exc:
        logging.error("Błąd TLS podczas nawiązywania połączenia z %s: %s", addr, exc.reason)
        raw_conn.close()
    except Exception as exc:
        logging.error("Nieoczekiwany błąd podczas obsługi klienta %s: %s", addr, exc)
        raw_conn.close()


def serve() -> None:
    port = listening_port()
    ssl_context = create_ssl_context()
    session_manager = SessionManager()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_sock.bind((HOST, port))
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                logging.error(
                    "Nie można zbindować portu %s — adres już w użyciu (EADDRINUSE).",
                    port,
                )
                logging.error(
                    "Użyj wolnego portu, np.: STATKI_PORT=5001 python3 -m server.main"
                )
                raise SystemExit(1) from exc
            raise
        server_sock.listen(BACKLOG)
        logging.info(
            "Serwer nasłuchuje na TLS *:%s (backlog=%s)",
            port,
            BACKLOG,
        )

        while True:
            raw_conn, addr = server_sock.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(raw_conn, addr, ssl_context, session_manager),
                daemon=True
            )
            client_thread.start()


def main() -> None:
    configure_logging()
    try:
        serve()
    except KeyboardInterrupt:
        logging.info("Zatrzymywanie serwera (Ctrl+C).")
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
