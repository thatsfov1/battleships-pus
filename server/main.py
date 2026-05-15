"""Serwer TCP gry Statki — szkielet nasłuchiwania i akceptacji połączeń."""

from __future__ import annotations

import errno
import logging
import logging.handlers
import os
import socket
import ssl
import sys
import threading
import signal
from typing import Final
from .session import SessionManager
from .handlers import ClientSession
from .security import SecurityManager
from . import config

def configure_logging() -> None:
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s", "%Y-%m-%d %H:%M:%S")
    
    file_handler = logging.handlers.RotatingFileHandler(config.LOG_PATH, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def create_ssl_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    
    context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
    
    try:
        context.load_cert_chain(certfile=config.CERT_PATH, keyfile=config.KEY_PATH)
    except FileNotFoundError as exc:
        logging.error("Nie znaleziono plików certyfikatów.")
        raise SystemExit(1) from exc
    return context


class Server:
    def __init__(self):
        self.stop_event = threading.Event()
        self.session_manager = SessionManager()
        self.security_manager = SecurityManager()
        self.server_sock = None

    def handle_client(self, raw_conn, addr, ssl_context):
        try:
            conn = ssl_context.wrap_socket(raw_conn, server_side=True)
            session = ClientSession(conn, addr, self.session_manager, self.security_manager)
            session.handle()
        except Exception as exc:
            logging.debug(f"Blad klienta {addr}: {exc}")
        finally:
            try:
                raw_conn.close()
            except:
                pass

    def run(self):
        configure_logging()
        ssl_context = create_ssl_context()
        
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.settimeout(1.0)
        
        try:
            self.server_sock.bind(("", config.PORT))
            self.server_sock.listen(5)
            logging.info(f"Serwer TLS nasluchuje na porcie {config.PORT}")
        except Exception as e:
            logging.error(f"Blad bind: {e}")
            return

        while not self.stop_event.is_set():
            try:
                raw_conn, addr = self.server_sock.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(raw_conn, addr, ssl_context),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    logging.error(f"Blad accept: {e}")

        logging.info("Zamykanie socketu serwera.")
        self.server_sock.close()

    def shutdown(self, signum, frame):
        logging.info("Sygnal shutdown... prosze czekac.")
        self.stop_event.set()


def main() -> None:
    srv = Server()
    signal.signal(signal.SIGINT, srv.shutdown)
    signal.signal(signal.SIGTERM, srv.shutdown)
    srv.run()


if __name__ == "__main__":
    main()
