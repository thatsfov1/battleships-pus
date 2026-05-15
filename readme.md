# Statki (Battleships)

Gra sieciowa „Statki” z architekturą klient–serwer. Serwer obsługuje połączenia TCP; katalogi `client/` i `tests/` są przygotowane pod dalszy rozwój, `certs/` — pod ewentualne certyfikaty TLS.

## Autorzy

- Yevhenii Kulikovskyi  
- Piotr Nieścior  

## Wymagania

- Python **3.10** lub nowszy  
- Pakiety — patrz `requirements.txt` (na razie tylko biblioteka standardowa)

## Uruchomienie serwera

Z katalogu głównego projektu:

```bash
python -m server.main
```

Alternatywnie:

```bash
cd server && python main.py
```

Serwer domyślnie nasłuchuje na porcie **5000** na wszystkich interfejsach (`0.0.0.0`). W konsoli pojawiają się wpisy o każdej zaakceptowanej parze adres:port klienta. Zatrzymanie: **Ctrl+C**.

## Struktura katalogów

| Katalog     | Opis                                      |
|------------|-------------------------------------------|
| `server/`  | Logika serwera (np. `main.py`)            |
| `client/`  | Klient gry                                 |
| `tests/`   | Testy                                      |
| `certs/`   | Certyfikaty (np. pod TLS) — do uzupełnienia |
