"""Konfiguracja klienta CLI Statki (nadpisywalna zmiennymi srodowiskowymi)."""

import os

HOST = os.getenv("BS_HOST", "localhost")
PORT = int(os.getenv("BS_PORT", os.getenv("PORT", "5000")))
# Certyfikat serwera uzywany jako zaufane CA (self-signed). Gdy brak pliku,
# klient laczy sie bez weryfikacji (z ostrzezeniem).
CA_CERT = os.getenv("BS_CA_CERT", os.path.join("certs", "server.crt"))
SERVER_HOSTNAME = os.getenv("BS_SERVER_HOSTNAME", "localhost")

CLIENT_VERSION = "1.0.0"
PING_INTERVAL = 10        # sekundy miedzy PING (zgodnie z protokolem 4.4)
CONNECT_TIMEOUT = 10      # timeout nawiazania polaczenia TCP
RECONNECT_ATTEMPTS = 3    # liczba prob reconnectu (protokol 4.3 / UC-06)
RECONNECT_DELAY = 5       # sekundy miedzy probami reconnectu
