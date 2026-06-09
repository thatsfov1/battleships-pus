# Protokół komunikacyjny - Przykłady

## 1. HELLO / WELCOME
Ustanowienie połączenia.

**Klient -> Serwer:**
```json
{
  "type": "HELLO",
  "msg_id": "1",
  "timestamp": 1715781000,
  "client_version": "1.0.0"
}
```

**Serwer -> Klient:**
```json
{
  "type": "WELCOME",
  "msg_id": "uuid-1",
  "timestamp": 1715781001,
  "server_version": "1.0.0"
}
```

## 2. AUTH
Uwierzytelnienie.

**Klient -> Serwer:**
```json
{
  "type": "AUTH",
  "msg_id": "2",
  "timestamp": 1715781005,
  "username": "user1",
  "password_hash": "sha256-hash-here"
}
```

**Serwer -> Klient:**
```json
{
  "type": "AUTH_OK",
  "msg_id": "uuid-2",
  "timestamp": 1715781006,
  "token": "jwt.token.here"
}
```

## 3. CREATE_GAME
Utworzenie nowej sesji.

**Klient -> Serwer:**
```json
{
  "type": "CREATE_GAME",
  "msg_id": "3",
  "timestamp": 1715781010
}
```

**Serwer -> Klient:**
```json
{
  "type": "ACK",
  "msg_id": "3",
  "timestamp": 1715781011
}
```

## 4. MOVE
Wykonanie ruchu w grze. Współrzędne podawane są jako pola `x`, `y` (0–9) na
najwyższym poziomie wiadomości.

**Klient -> Serwer:**
```json
{
  "type": "MOVE",
  "msg_id": "4",
  "timestamp": 1715781020,
  "x": 5,
  "y": 2
}
```

**Serwer -> Klient (potwierdzenie odbioru):**
```json
{
  "type": "ACK",
  "msg_id": "4",
  "timestamp": 1715781021
}
```

**Serwer -> obaj gracze (wynik ruchu):**
```json
{
  "type": "MOVE_RESULT",
  "msg_id": "uuid-mr",
  "timestamp": 1715781022,
  "x": 5,
  "y": 2,
  "result": "HIT",
  "by": "user1",
  "next_turn": "user2"
}
```
`result` przyjmuje wartości `HIT`, `MISS` lub `SUNK`. Pole `by` wskazuje
strzelającego, a `next_turn` gracza, do którego należy kolejna tura
(`null` po zakończeniu gry).

## 5. GAME_START
Rozpoczęcie rozgrywki po dołączeniu drugiego gracza. Serwer dołącza własną
planszę gracza (`your_board`) oraz informację, czyja jest pierwsza tura.

**Serwer -> obaj gracze:**
```json
{
  "type": "GAME_START",
  "msg_id": "uuid-gs",
  "timestamp": 1715781015,
  "session_id": "game123",
  "players": ["user1", "user2"],
  "current_turn": "user1",
  "your_board": [["", "S", "S", "..."]]
}
```

## 6. GAME_END
Zakończenie gry.

**Serwer -> Klient:**
```json
{
  "type": "GAME_END",
  "msg_id": "uuid-99",
  "timestamp": 1715781100,
  "reason": "VICTORY",
  "winner": "user1"
}
```

## 7. ERROR
Komunikaty błędów. Kody m.in.: `NOT_YOUR_TURN`, `INVALID_MOVE`,
`SESSION_NOT_FOUND`, `RATE_LIMIT`, `DUPLICATE_MESSAGE`, `INVALID_JSON`.

**Serwer -> Klient:**
```json
{
  "type": "ERROR",
  "msg_id": "uuid-err",
  "timestamp": 1715781200,
  "code": "RATE_LIMIT",
  "message": "Too many requests"
}
```

## 8. BYE
Poprawne zakończenie sesji przez klienta (graceful disconnect). Po odebraniu
`BYE` serwer zamyka połączenie TCP/TLS.

**Klient -> Serwer:**
```json
{
  "type": "BYE",
  "msg_id": "99",
  "timestamp": 1715781300
}
```
