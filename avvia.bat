@echo off
REM ============================================================
REM  Pollini & Sintomi - avvio rapido
REM  Doppio click su questo file per avviare l'app.
REM  Al primo avvio crea l'ambiente e installa le dipendenze.
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Primo avvio: creazione ambiente virtuale...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRORE: Python non trovato. Installa Python 3.10+ da https://www.python.org
        echo e assicurati di spuntare "Add Python to PATH".
        echo.
        pause
        exit /b 1
    )
    echo Installazione dipendenze...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
