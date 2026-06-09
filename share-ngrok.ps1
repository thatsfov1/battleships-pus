<#
  Udostepnia gre Statki w internecie przez ngrok (Windows / PowerShell).

  Dzieki proxy WebSocket w Vite (sciezka /ws) wystarczy JEDEN tunel na port 5173:
  i strona, i WebSocket ida przez ten sam publiczny adres ngrok.

  Co robi skrypt:
    1. uruchamia caly stos lokalny (serwer gry + most WS + dev server React)
       wywolujac run-all.ps1,
    2. otwiera tunel ngrok na port 5173 i wypisuje publiczny adres.

  Uzycie (z katalogu battleships-pus):
    powershell -ExecutionPolicy Bypass -File share-ngrok.ps1

  Wymagania:
    - ngrok zainstalowany i skonfigurowany authtokenem
      (jednorazowo: ngrok config add-authtoken <TWOJ_TOKEN> z dashboardu ngrok).
  Adres https://...ngrok-free.app wyslij znajomym — kazdy otwiera go w przegladarce
  (przy pierwszym wejsciu ngrok pokazuje ekran ostrzezenia, kliknij "Visit Site").
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# Sprawdz, czy ngrok jest dostepny
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "Nie znaleziono 'ngrok' w PATH. Zainstaluj: choco install ngrok" -ForegroundColor Red
    exit 1
}

# 1) Podnies caly stos lokalny (3 okna: serwer, most, React)
Write-Host "Uruchamiam stos lokalny (run-all.ps1)..." -ForegroundColor Cyan
& (Join-Path $root 'run-all.ps1')

# Daj dev serverowi React chwile na start zanim wpustimy ruch z tunelu
Start-Sleep -Seconds 4

# 2) Otworz tunel ngrok na port 5173 (na pierwszym planie — widac publiczny URL)
Write-Host ""
Write-Host "Otwieram tunel ngrok na http://localhost:5173 ..." -ForegroundColor Cyan
Write-Host "Adres 'Forwarding https://...ngrok-free.app' wyslij znajomym." -ForegroundColor Yellow
Write-Host ""
ngrok http 5173
