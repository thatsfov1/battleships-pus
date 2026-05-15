# Statki (Battleships)

Gra sieciowa „Statki” z architekturą klient–serwer. Serwer obsługuje szyfrowane połączenia TLS; katalogi `client/` i `tests/` są przygotowane pod dalszy rozwój.

## Autorzy

- Yevhenii Kulikovskyi  
- Piotr Nieścior  

## Wymagania

- Python **3.10** lub nowszy  
- OpenSSL (do generowania certyfikatów)
- Pakiety — patrz `requirements.txt` (na razie tylko biblioteka standardowa)

## Konfiguracja TLS

Przed pierwszym uruchomieniem serwera należy wygenerować self-signed certyfikat:

```bash
chmod +x certs/generate_certs.sh
./certs/generate_certs.sh
```

Skrypt utworzy pliki `server.key` oraz `server.crt` w katalogu `certs/`.

## Uruchomienie serwera

Z katalogu głównego projektu:

```bash
python3 -m server.main
```

Serwer domyślnie nasłuchuje na porcie **5000** i **wymaga połączenia TLS**. Próby połączenia bez szyfrowania zostaną odrzucone. W konsoli pojawiają się wpisy o każdej zaakceptowanej sesji TLS. Zatrzymanie: **Ctrl+C**.

Można zmienić port nasłuchiwania za pomocą zmiennej środowiskowej:
```bash
STATKI_PORT=5001 python3 -m server.main
```

## Struktura katalogów

| Katalog     | Opis                                      |
|------------|-------------------------------------------|
| `server/`  | Logika serwera (np. `main.py`)            |
| `client/`  | Klient gry                                 |
| `tests/`   | Testy                                      |
| `certs/`   | Certyfikaty i klucze TLS                   |
