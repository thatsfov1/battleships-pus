# Jak zagrać w Statki przez internet (ngrok)

Kompletny przewodnik od zera. Gracie z dowolnego miejsca na świecie, a **znajomi
nie muszą nic instalować** — wystarczy przeglądarka i link.

> **Zasada:** jedna osoba (HOST) uruchamia całą grę u siebie i udostępnia ją
> jednym publicznym adresem przez darmowy tunel **ngrok**. Reszta tylko otwiera
> ten link w przeglądarce. Dzięki proxy WebSocket wystarczy **jeden tunel**
> (port 5173) — i strona, i komunikacja gry idą przez ten sam adres.

Role:
- **HOST** — uruchamia grę i wystawia ją do internetu. Może też grać.
- **GRACZ** — dostaje link i otwiera go w przeglądarce. Nic nie instaluje.

---

## CZĘŚĆ A — HOST: przygotowanie (jednorazowo)

### A.1 Zainstaluj wymagane programy
- **Python 3.12+** — https://www.python.org/downloads/
  (przy instalacji zaznacz **„Add Python to PATH"**)
- **Node.js 18+** — https://nodejs.org (wersja LTS)
- **ngrok** — https://ngrok.com/download (albo `choco install ngrok`)

Sprawdź w PowerShell, że wszystko jest widoczne:
```powershell
python --version
node --version
ngrok version
```

### A.2 Skonfiguruj ngrok (raz)
Załóż darmowe konto na https://ngrok.com, skopiuj swój token z panelu
(sekcja **„Your Authtoken"**) i ustaw go:
```powershell
ngrok config add-authtoken <TWOJ_TOKEN>
```

### A.3 Zainstaluj zależności projektu (raz)
W PowerShell wejdź do folderu projektu:
```powershell
cd C:\sciezka\do\battleships-pus
python -m pip install -r requirements.txt
cd web; npm install; cd ..
```
(React i tak doinstaluje się sam przy pierwszym uruchomieniu, ale lepiej zrobić to teraz.)

---

## CZĘŚĆ B — HOST: uruchom grę i tunel

W folderze `battleships-pus`:
```powershell
powershell -ExecutionPolicy Bypass -File share-ngrok.ps1
```

Skrypt:
1. uruchamia **serwer gry**, **most WebSocket** i **dev server React** (3 okna),
2. otwiera **tunel ngrok** na port 5173.

W oknie ngrok znajdź linię:
```
Forwarding   https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5173
```
Adres `https://xxxx....ngrok-free.app` to **link do gry**.

> ⚠️ Zostaw wszystkie okna otwarte przez całą rozgrywkę. Darmowy adres ngrok
> **zmienia się przy każdym uruchomieniu** — po restarcie wyślij znajomemu nowy link.

---

## CZĘŚĆ C — GRACZE: dołącz do gry

> Robi to **każdy gracz** (host też, jeśli gra). Nic nie instalujesz.

1. Otwórz link `https://xxxx.ngrok-free.app` od hosta w przeglądarce.
2. Przy pierwszym wejściu ngrok pokaże ekran ostrzeżenia → kliknij **„Visit Site"**.
3. Zaloguj się testowym kontem — **każdy komputer innym kontem**:
   - Gracz 1 → login **user1**, hasło **pass1**
   - Gracz 2 → login **user2**, hasło **pass2**

---

## CZĘŚĆ D — Rozgrywka

1. Jeden gracz klika **„Utwórz grę"** → zobaczy „Oczekiwanie na przeciwnika…".
2. Drugi gracz klika **„Dołącz do gry"**.

Serwer **automatycznie paruje** obu graczy — nie ma żadnego kodu/ID do przepisywania.
Po sparowaniu zaczyna się rozstawienie floty, a potem naprzemienne strzały
(klikasz pola planszy przeciwnika). Wygrywa ten, kto pierwszy zatopi całą flotę wroga.

---

## Najczęstsze problemy

| Objaw | Przyczyna i rozwiązanie |
|---|---|
| `ngrok: command not found` | Zainstaluj ngrok (`choco install ngrok`) i ustaw authtoken (A.2). |
| ngrok pisze o braku authtokena | Wykonaj `ngrok config add-authtoken <TWOJ_TOKEN>` (A.2). |
| Strona prosi o „Visit Site" | Normalne dla darmowego ngroka — kliknij przycisk, by przejść dalej. |
| „This host is not allowed" | W `web/vite.config.js` musi być `allowedHosts: true` (już ustawione). |
| „Utracono połączenie z mostem" | Most/serwer nie działają. Sprawdź, czy 3 okna z `share-ngrok.ps1` nadal są otwarte; odśwież stronę (F5). |
| Znajomy nie może wejść | Tunel ngrok został zamknięty albo link jest stary — wyślij aktualny adres z okna ngrok. |
| „Dołącz" nic nie robi | Drugi gracz nie kliknął jeszcze „Utwórz grę", albo obaj zalogowali się na to samo konto. Użyjcie user1 i user2. |
| `ModuleNotFoundError` u hosta | Brak zależności — `python -m pip install -r requirements.txt` (A.3). |

---

## Uwagi

- **Tylko HOST** uruchamia `share-ngrok.ps1`. Gracze niczego nie odpalają —
  dostają gotowy link.
- **Gracze nie ruszają routera** — łączą się wychodząco przez przeglądarkę,
  NAT to przepuszcza. Tylko host wystawia port (przez ngrok).
- **W tej samej sieci Wi-Fi** tunel jest zbędny: host odpala `run-all.ps1`,
  a znajomy wchodzi pod `http://<adres-IP-hosta>:5173` (`ipconfig` → „IPv4 Address";
  w zaporze Windows zezwól na port 5173).
- **Bezpieczeństwo (projekt studencki):** certyfikat i klucz TLS są w repo
  (`certs/`), więc do produkcji wygenerowałbyś własne i nie trzymał ich w repo.

Szczegóły techniczne i inne sposoby uruchomienia: [readme.md](readme.md).
