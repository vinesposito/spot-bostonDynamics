# Script di PowerShell per impostare le variabili d'ambiente per l'SDK di Spot
# Sostituisci 'tuo_username' e 'tua_password' con le tue credenziali reali.

Write-Host "Impostazione delle variabili d'ambiente per Spot..." -ForegroundColor Yellow

# Indirizzo IP connessione WiFi del robot
$env:BOSDYN_CLIENT_HOSTNAME = "192.168.80.3"

# Indirizzo IP connessione Ethernet del robot
#$env:BOSDYN_CLIENT_HOSTNAME = "10.0.0.3"

$env:BOSDYN_CLIENT_USERNAME = "user"
$env:BOSDYN_CLIENT_PASSWORD = "wi4hiyphzu7b"


Write-Host "Variabili d'ambiente impostate correttamente per la sessione corrente." -ForegroundColor Green
Write-Host "" # Aggiunge una linea vuota per leggibilità
Write-Host "Username impostato: $($env:BOSDYN_CLIENT_USERNAME)"
Write-Host "La password è stata impostata ma non viene mostrata per sicurezza."