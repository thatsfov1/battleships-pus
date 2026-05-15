# Statki (Battleships) - Backend Serwer

Serwer gry wieloosobowej "Statki" zaimplementowany w Pythonie, wspierający bezpieczną komunikację TLS, uwierzytelnianie JWT oraz mechanizmy niezawodności połączeń.

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
- **Reconnect**: Możliwość powrotu do gry w ciągu 60 sekund po utracie połączenia.
- **Security**: Rate limiting, replay attack protection, TLS hardening.
- **Reliability**: Mechanizm ACK dla kluczowych wiadomości.

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
3. **Testy**:
   ```bash
   make test
   ```

## Wymagania
- Python 3.12+
- OpenSSL (do certyfikatów)

## Struktura Katalogów
- `server/`: Kod źródłowy serwera.
- `certs/`: Skrypt i wygenerowane certyfikaty TLS.
- `docs/`: Dokumentacja projektu.
- `logs/`: Logi systemowe (z rotacją).
- `tests/`: Testy jednostkowe.

## Autorzy
- Yevhenii Kulikovskyi
- Piotr Nieścior
