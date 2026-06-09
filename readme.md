# Statki (Battleships) - Serwer + Klient CLI

Gra wieloosobowa "Statki" zaimplementowana w Pythonie: serwer TCP/TLS oraz tekstowy klient CLI, wspierające bezpieczną komunikację TLS, uwierzytelnianie JWT oraz mechanizmy niezawodności połączeń.

## Architektura Systemu

Serwer opiera się na architekturze wielowątkowej (wątek na klienta) i wykorzystuje stos technologiczny:
- **TLS 1.2+**: Szyfrowanie całej komunikacji.
- **JWT**: Bezpieczne sesje użytkowników.
- **SQLite**: Przechowywanie haseł (SHA-256).
- **Heartbeat (Keepalive)**: Monitorowanie aktywności klientów.

Szczegółowy opis architektury znajduje się w `docs/server_architecture.md`.

## Protokół Komunikacyjny

Komunikacja odbywa się za pomocą wiadomości JSON zakończonych znakiem nowej linii (`\n`). 
Przykłady komunikatów i flow protokołu dostępne są w `docs/protocol_examples.md`.

## Funkcje
- **Rozgrywka 2-osobowa**: Pełna logika Statków — losowe rozstawienie floty (`5,4,3,3,2`) na planszy 10×10, strzały z wynikiem `HIT`/`MISS`/`SUNK`, naprzemienne tury, wykrywanie zwycięstwa.
- **Klient CLI**: Logowanie, lobby (utwórz/dołącz), render obu plansz, wprowadzanie strzałów w formacie `B5`.
- **Reconnect**: Możliwość powrotu do gry w ciągu 60 sekund po utracie połączenia (walkower po przekroczeniu czasu).
- **Security**: Rate limiting, replay attack protection, TLS hardening.
- **Reliability**: Mechanizm ACK dla kluczowych wiadomości, keep-alive PING/PONG, serializacja zapisu TLS per-połączenie.

## Szybki start (Docker)

1. Skopiuj przykład konfiguracji:
   ```bash
   cp .env.example .env
   ```
2. Uruchom kontener:
   ```bash
   docker-compose up --build
   ```

## Uruchomienie Lokalne (Makefile)

1. **Inicjalizacja** (instalacja paczek, DB, certyfikaty):
   ```bash
   make init
   ```
2. **Start serwera**:
   ```bash
   make run
   ```
3. **Start klienta** (w osobnym terminalu, dla każdego gracza):
   ```bash
   make run-client
   # lub: python -m client.main [host] [port]
   ```
   Domyślnie łączy się z `localhost:5000`. Konta testowe: `user1/pass1`, `user2/pass2`.
   Aby zagrać partię, uruchom dwóch klientów: jeden wybiera „Utwórz grę", drugi „Dołącz do gry".
4. **Testy**:
   ```bash
   make test
   ```

## Frontend webowy (React)

Przeglądarka nie może otworzyć surowego gniazda TCP/TLS, dlatego między aplikacją React
a serwerem gry działa **most WebSocket↔TCP** (`ws_gateway.py`). Schemat:

```
[React] --WebSocket--> [ws_gateway.py] --TLS/JSON-over-TCP--> [serwer gry]
```

Uruchomienie (każde w osobnym terminalu, z katalogu `battleships-pus`):

1. **Serwer gry**: `python -m server.main`
2. **Most WebSocket** (domyślnie `ws://localhost:8765`):
   ```bash
   python ws_gateway.py
   # lub: make gateway
   ```
3. **Aplikacja React** (dev server na `http://localhost:5173`):
   ```bash
   cd web
   npm install   # jednorazowo
   npm run dev
   ```

Otwórz `http://localhost:5173` w dwóch kartach (dla dwóch graczy), zaloguj się
(`user1/pass1`, `user2/pass2`), jeden „Utwórz grę", drugi „Dołącz do gry".
Adres mostu można zmienić zmienną `VITE_GATEWAY_URL`.

## Wymagania
- Python 3.12+ (serwer, klient CLI, most)
- Node.js 18+ i npm (frontend React)
- OpenSSL (do certyfikatów)

## Struktura Katalogów
- `server/`: Kod źródłowy serwera (sieć, protokół, sesje, silnik gry `game.py`).
- `client/`: Klient CLI (`network.py` — warstwa sieciowa, `game_ui.py` — render/parsowanie, `main.py` — pętla gry).
- `web/`: Frontend React (Vite). Komponenty: `Login`, `Lobby`, `Board`, `Game`; hook `useGameSocket`.
- `ws_gateway.py`: Most WebSocket↔TCP dla aplikacji webowej.
- `certs/`: Skrypt i wygenerowane certyfikaty TLS.
- `docs/`: Dokumentacja projektu.
- `logs/`: Logi systemowe (z rotacją).
- `tests/`: Testy jednostkowe.

## Autorzy
- Yevhenii Kulikovskyi
- Piotr Nieścior
