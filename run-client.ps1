<#
  KLIENT (gracz) — uruchamia most WebSocket + aplikacje React i laczy je
  ze WSPOLNYM, zdalnym serwerem gry. Ten skrypt odpala KAZDY gracz na swoim
  komputerze. NIE uruchamia lokalnego serwera gry.

  >>> USTAW RAZ: adres serwera gry (od osoby hostujacej) <<<
#>

# ============================================================================
#  ADRES SERWERA GRY  — wpisz tutaj adres uzyskany przez hosta (run-server.ps1)
#  Przyklad z playit.gg:  '147-185-221-10.ip.linodeusercontent.com'  port 12345
#  Mozna tez nadpisac zmienna srodowiskowa BS_HOST / BS_PORT.
# ============================================================================
$SERVER_HOST = 'WPISZ-TU-ADRES-SERWERA'
$SERVER_PORT = '5000'
# ============================================================================

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

# Pozwol nadpisac adres zmiennymi srodowiskowymi (wygodne do testow).
if ($env:BS_HOST) { $SERVER_HOST = $env:BS_HOST }
if ($env:BS_PORT) { $SERVER_PORT = $env:BS_PORT }

if ($SERVER_HOST -eq 'WPISZ-TU-ADRES-SERWERA' -or [string]::IsNullOrWhiteSpace($SERVER_HOST)) {
    Write-Host "BLAD: nie ustawiono adresu serwera gry." -ForegroundColor Red
    Write-Host "Otworz run-client.ps1 i w linii `$SERVER_HOST wpisz adres od hosta," -ForegroundColor Yellow
    Write-Host "albo uruchom:  `$env:BS_HOST='adres'; .\run-client.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Lacze sie z serwerem gry: $SERVER_HOST`:$SERVER_PORT" -ForegroundColor Cyan

# 1) Most WebSocket (lokalnie). Laczy sie WYCHODZACO do zdalnego serwera gry,
#    wiec nie trzeba otwierac zadnych portow w routerze gracza.
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root'; `$env:BS_HOST='$SERVER_HOST'; `$env:BS_PORT='$SERVER_PORT'; Write-Host '== MOST WEBSOCKET -> $SERVER_HOST ==' -ForegroundColor Green; python ws_gateway.py"
)

# 2) Dev server React (http://localhost:5173). Przegladarka laczy sie z LOKALNYM
#    mostem (ws://localhost:8765), wiec adres React pozostaje bez zmian.
$web = Join-Path $root 'web'
if (-not (Test-Path (Join-Path $web 'node_modules'))) {
    Write-Host "Brak node_modules w web/ - instaluje zaleznosci (npm install)..." -ForegroundColor Yellow
    Push-Location $web; npm install; Pop-Location
}
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$web'; Write-Host '== REACT (Vite) ==' -ForegroundColor Green; npm run dev"
)

Write-Host ""
Write-Host "Gotowe. Otworz http://localhost:5173 i zaloguj sie." -ForegroundColor Cyan
Write-Host "Jeden gracz wybiera 'Utworz gre', drugi 'Dolacz do gry'." -ForegroundColor Cyan
Write-Host "WAZNE: jeden komputer loguje sie jako user1/pass1, drugi jako user2/pass2." -ForegroundColor Yellow
