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
Wykonanie ruchu w grze.

**Klient -> Serwer:**
```json
{
  "type": "MOVE",
  "msg_id": "4",
  "timestamp": 1715781020,
  "move": {"x": 5, "y": 2}
}
```

**Serwer -> Klient:**
```json
{
  "type": "ACK",
  "msg_id": "4",
  "timestamp": 1715781021
}
```

## 5. GAME_END
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

## 6. ERROR
Komunikaty błędów.

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
