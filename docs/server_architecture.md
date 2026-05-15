# Architektura Serwera Battleships

## Komponenty Systemu

1. **Warstwa Sieciowa (`server/main.py`, `server/protocol.py`)**
   - Obsługa gniazd TCP/TLS.
   - Serializacja/Deserializacja JSON (warstwa protokołu).
   - Multi-threading: Każdy klient w osobnym wątku.

2. **Bezpieczeństwo (`server/security.py`, `server/auth.py`)**
   - TLS 1.2+ z bezpiecznymi szyframi.
   - Uwierzytelnianie użytkowników (SQLite + SHA256).
   - Tokeny JWT dla sesji.
   - Rate limiting & Replay protection.

3. **Logika Gry i Sesji (`server/session.py`, `server/reconnect.py`)**
   - Zarządzanie lobby i parami graczy.
   - Obsługa rozłączeń i reconnectu (60s).
   - Maszyna stanu gry (GameSession).

4. **Niezawodność (`server/keepalive.py`)**
   - Mechanizm Heartbeat (PING/PONG).
   - Mechanizm ACK dla kluczowych wiadomości.

## Schemat Połączenia

```text
[Klient] <--- TLS 1.2 ---> [Główny Wątek Serwera]
                                |
                                v
                       [Wątek Obsługi Klienta]
                                |
         +----------------------+----------------------+
         |                      |                      |
    [Keepalive]         [Security Check]        [Game Handler]
```

## Baza Danych
SQLite z tabelą `users`:
- `id`: INTEGER PK
- `username`: TEXT UNIQUE
- `password_hash`: TEXT (SHA256)
