# Jak zagrać w Statki przez internet — instrukcja end-to-end

Kompletny przewodnik od zera. Dwa dowolne komputery, gdziekolwiek na świecie.

> **Zasada:** oba komputery łączą się z **jednym wspólnym serwerem gry**. Jedna
> osoba (host) ten serwer uruchamia i udostępnia, reszta tylko się łączy. Tak
> działa każda gra sieciowa — bez wspólnego serwera komputery nie mają jak się
> odnaleźć.

Role:
- **HOST** — uruchamia serwer gry i wystawia go do internetu. Może też grać.
- **GRACZ** — tylko się łączy. (Host również wykonuje kroki „GRACZ", żeby grać.)

---

## CZĘŚĆ 0 — Przygotowanie (każdy komputer, raz)

Wykonują **wszyscy** (host i gracze), bo każdy uruchamia coś lokalnie.

### 0.1 Zainstaluj wymagane programy
- **Python 3.12+** — https://www.python.org/downloads/
  (przy instalacji zaznacz **„Add Python to PATH"**)
- **Node.js 18+** — https://nodejs.org (wersja LTS)

Sprawdź w PowerShell, że są widoczne:
```powershell
python --version
node --version
```

### 0.2 Pobierz projekt
Skopiuj cały folder `battleships-pus` na komputer (np. tak jak masz teraz na
`C:\Users\...\statki\battleships-pus`).

### 0.3 Zainstaluj zależności
W PowerShell wejdź do folderu projektu i zainstaluj biblioteki:
```powershell
cd C:\sciezka\do\battleships-pus
python -m pip install -r requirements.txt
```
React zainstaluje się sam przy pierwszym uruchomieniu `run-client.ps1`
(albo ręcznie: `cd web; npm install`).

---

## CZĘŚĆ A — HOST: uruchom serwer gry

> Robi to **jedna osoba**.

### A.1 Wystartuj serwer
W folderze `battleships-pus`:
```powershell
powershell -ExecutionPolicy Bypass -File run-server.ps1
```
Skrypt utworzy bazę kont (przy pierwszym uruchomieniu) i wystartuje serwer.
Zobaczysz w oknie:
```
Serwer TLS nasluchuje na porcie 5000
```
**Zostaw to okno otwarte** — serwer musi działać przez całą rozgrywkę.

---

## CZĘŚĆ B — HOST: wystaw serwer do internetu (playit.gg)

Serwer działa, ale na razie tylko lokalnie. Trzeba dać mu publiczny adres.
Serwer używa surowego TCP/TLS (nie HTTP), więc potrzebny jest **tunel TCP**.
Najprościej i za darmo: **playit.gg** (daje stały adres).

### B.1 Załóż konto i pobierz program
1. Wejdź na https://playit.gg → załóż darmowe konto.
2. Pobierz i zainstaluj **playit** na Windows (przycisk „Download").
3. Uruchom program — otworzy stronę logowania w przeglądarce, zaloguj się
   (program połączy się z Twoim kontem).

### B.2 Utwórz tunel TCP na port 5000
W panelu playit.gg (w przeglądarce):
1. **Add Tunnel** / „Create Tunnel".
2. Typ: **TCP** (NIE „Minecraft", NIE „HTTP").
3. **Local port / Local address**: `5000` (czyli `127.0.0.1:5000`).
4. Zapisz.

> Układ panelu playit.gg bywa aktualizowany — szukaj opcji „custom TCP tunnel"
> wskazującej na lokalny port 5000.

### B.3 Odczytaj publiczny adres
playit.gg pokaże publiczny adres tunelu, np.:
```
adres:  147-x-x-x.something.playit.gg
port:   12345
```
**To jest adres Twojego serwera.** Przekaż go drugiemu graczowi
(i sobie — będzie potrzebny w Części C). Zostaw program playit uruchomiony.

---

## CZĘŚĆ C — GRACZE: połącz się z serwerem

> Robi to **każdy gracz osobno** (host też, jeśli gra).

### C.1 Wpisz adres serwera
Otwórz plik `run-client.ps1` w folderze `battleships-pus` (np. w Notatniku)
i na górze wpisz adres oraz port z Części B.3:
```powershell
$SERVER_HOST = '147-x-x-x.something.playit.gg'   # adres od hosta
$SERVER_PORT = '12345'                           # port od hosta
```
Zapisz plik.

### C.2 Uruchom klienta
W folderze `battleships-pus`:
```powershell
powershell -ExecutionPolicy Bypass -File run-client.ps1
```
Otworzą się **dwa okna**: most WebSocket (łączy się z serwerem hosta) oraz
React (Vite). Przy pierwszym razie React zrobi `npm install` — chwilę to trwa.

Gdy zobaczysz w oknie React komunikat typu `Local: http://localhost:5173/`,
można grać.

---

## CZĘŚĆ D — Rozgrywka

### D.1 Otwórz grę
Każdy gracz otwiera w przeglądarce:
```
http://localhost:5173
```

### D.2 Zaloguj się — RÓŻNE konta na różnych komputerach
- Komputer 1 → login **user1**, hasło **pass1**
- Komputer 2 → login **user2**, hasło **pass2**

> Konta muszą być różne — na jednym koncie nie zalogują się dwie osoby naraz.

### D.3 Połączcie się w grę
- Jeden gracz klika **„Utwórz grę"** → zobaczy „Oczekiwanie na przeciwnika…"
- Drugi gracz klika **„Dołącz do gry"**

Serwer **automatycznie paruje** obu graczy — nie ma żadnego kodu/ID do
przepisywania. Po sparowaniu zaczyna się faza rozstawienia floty, potem
naprzemienne strzały aż do zatopienia całej floty przeciwnika.

---

## Najczęstsze problemy

| Objaw | Przyczyna i rozwiązanie |
|---|---|
| „Utracono połączenie z mostem" | Most nie połączył się z serwerem. Sprawdź: czy host ma uruchomiony `run-server.ps1` i playit, oraz czy w `run-client.ps1` adres/port są poprawne. Po poprawkach **odśwież** stronę (F5). |
| `ModuleNotFoundError` | Nie zainstalowano zależności — wykonaj `python -m pip install -r requirements.txt` (Część 0.3). |
| Most pisze „nie udalo sie polaczyc z serwerem gry" | Zły adres/port w `run-client.ps1`, albo serwer/playit nie działają u hosta. |
| „Dołącz" nic nie robi | Drugi gracz nie kliknął jeszcze „Utwórz grę", albo obaj zalogowali się na to samo konto. Użyjcie user1 i user2. |
| React nie startuje | W folderze `web` zrób raz `npm install`. |

## Uwagi
- **Tylko host** uruchamia `run-server.ps1`. Jeśli każdy odpali własny serwer,
  traficie na osobne, niepołączone serwery (to był pierwotny problem).
- **Gracze nie ruszają routera** — most łączy się wychodząco, NAT to przepuszcza.
  Tylko host wystawia port (przez playit.gg).
- **W tej samej sieci Wi-Fi** możesz pominąć playit.gg: jako `$SERVER_HOST` podaj
  lokalny adres IP hosta (`ipconfig` → „IPv4 Address"), a w zaporze Windows
  zezwól na ruch przychodzący na porcie 5000.
- **Bezpieczeństwo (projekt studencki):** certyfikat i klucz TLS są w repo
  (`certs/`), więc do produkcji wygenerowałbyś własne i nie trzymał ich w repo.
