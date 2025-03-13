# Imposta l'errore se qualcosa va storto
$ErrorActionPreference = "Stop"

# Percorso del file requirements.txt (se si trova nella stessa cartella dello script)
$requirementsFile = "$PSScriptRoot\requirements.txt"

# Funzione per verificare se un comando esiste
function Command-Exists {
    param ($cmd)
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Host "Controllo se Python è già installato..."

# Controlla se Python è installato
if (-not (Command-Exists python)) {
    Write-Host "Python non trovato! Installazione in corso..."
    
    # Controlla se winget è disponibile
    if (Command-Exists winget) {
        Write-Host "Installando Python con winget..."
        winget install Python.Python --silent

        # Aggiorna la sessione per riconoscere Python
        $env:Path += ";C:\Users\$env:UserName\AppData\Local\Microsoft\WindowsApps"
        
        # Ricarica il profilo utente per riconoscere Python
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")
    } else {
        Write-Host "winget non disponibile! Scaricare e installare Python manualmente da https://www.python.org/downloads/"
        Exit 1
    }
}

# Verifica l'installazione di Python
if (Command-Exists python) {
    Write-Host "Python installato correttamente!"
    Write-Host "Versione di Python: $(python --version)"
} else {
    Write-Host "Errore durante l'installazione di Python!"
    Exit 1
}

Write-Host "Aggiornamento di pip..."
python -m pip install --upgrade pip

# Controlla se il file requirements.txt esiste
if (Test-Path $requirements.txt) {
    Write-Host "Trovato requirements.txt! Installazione delle dipendenze..."
    pip install -r $requirements.txt
} else {
    Write-Host "Nessun file requirements.txt trovato, verranno installati i pacchetti di base..."
    pip install ttkbootstrap paramiko requests urllib3 pillow
}

Write-Host "Installazione completata!"
Write-Host "Pacchetti installati:"
pip list
