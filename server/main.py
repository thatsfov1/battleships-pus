"""Serwer TCP gry Statki — szkielet nasłuchiwania i akceptacji połączeń."""

from __future__ import annotations

import errno
import logging
import os
import socket
import sys
from typing import Final

HOST: Final[str] = ""  # wszystkie interfejsy
DEFAULT_PORT: Final[int] = 5000
BACKLOG: Final[int] = 5


def listening_port() -> int:
    return int(os.environ.get("STATKI_PORT", str(DEFAULT_PORT)))


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def serve() -> None:
    port = listening_port()
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
            "Serwer nasłuchuje na TCP *:%s (backlog=%s)",
            port,
            BACKLOG,
        )

        while True:
            conn, addr = server_sock.accept()
            with conn:
                logging.info("Zaakceptowano połączenie od %s:%s", addr[0], addr[1])


def main() -> None:
    configure_logging()
    try:
        serve()
    except KeyboardInterrupt:
        logging.info("Zatrzymywanie serwera (Ctrl+C).")
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
