<#
  Uruchamia caly stos webowy gry Statki jedna komenda (Windows / PowerShell):
    - serwer gry        (python -m server.main)
    - most WebSocket    (python ws_gateway.py)
    - dev server React  (npm run dev w katalogu web)

  Uzycie (z katalogu battleships-pus):
    powershell -ExecutionPolicy Bypass -File run-all.ps1

  Kazdy proces startuje w osobnym oknie terminala, dzieki czemu widac logi
  i mozna kazdy zamknac z osobna (Ctrl+C w danym oknie).
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Write-Host "Startuje stos webowy z: $root" -ForegroundColor Cyan

# 1) Serwer gry (TCP/TLS na :5000)
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root'; Write-Host '== SERWER GRY ==' -ForegroundColor Green; python -m server.main"
)

# Daj serwerowi chwile na podniesienie gniazda zanim wstanie most
Start-Sleep -Seconds 2

# 2) Most WebSocket <-> TCP (ws://localhost:8765)
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root'; Write-Host '== MOST WEBSOCKET ==' -ForegroundColor Green; python ws_gateway.py"
)

# 3) Dev server React (http://localhost:5173)
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
Write-Host "Gotowe. Otwarto 3 okna terminala." -ForegroundColor Cyan
Write-Host "Otworz http://localhost:5173 w dwoch kartach (user1/pass1, user2/pass2)." -ForegroundColor Cyan
