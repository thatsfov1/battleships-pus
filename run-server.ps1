<#
  SERWER GRY (host) — uruchamia TYLKO serwer gry na porcie 5000.
  Ten skrypt odpala JEDNA osoba, ktora hostuje rozgrywke. Gracze (w tym Ty)
  laacza sie potem przez run-client.ps1.

  Uzycie (z katalogu battleships-pus):
    powershell -ExecutionPolicy Bypass -File run-server.ps1

  Aby serwer byl osiagalny z internetu, port 5000 musi byc publicznie dostepny.
  Najprostsza darmowa metoda bez grzebania w routerze: tunel playit.gg
  (patrz JAK-GRAC-W-INTERNECIE.md).
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

Write-Host "== SERWER GRY (host) ==" -ForegroundColor Cyan

# Baza danych z kontami testowymi (user1/pass1, user2/pass2) — tworzona raz.
if (-not (Test-Path (Join-Path $root 'users.db'))) {
    Write-Host "Tworze baze danych (users.db)..." -ForegroundColor Yellow
    python init_db.py
}

$port = if ($env:PORT) { $env:PORT } else { '5000' }
Write-Host "Serwer gry nasluchuje na porcie $port (wszystkie interfejsy)." -ForegroundColor Green
Write-Host "Udostepnij ten port w internecie (np. tunel playit.gg) i podaj graczom" -ForegroundColor Green
Write-Host "uzyskany adres -> wpiszcie go w run-client.ps1 jako `$SERVER_HOST." -ForegroundColor Green
Write-Host ""

# Serwer gry juz binduje na ("", PORT) = wszystkie interfejsy, wiec jest
# osiagalny z sieci od razu, gdy tylko port zostanie wystawiony na zewnatrz.
python -m server.main
