@echo off
REM ============================================================
REM  Pollini & Sintomi - creazione eseguibile (.exe)
REM  Doppio click per generare dist\PolliniSintomi.exe
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creazione ambiente virtuale...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRORE: Python non trovato. Installa Python 3.10+ da https://www.python.org
        echo.
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo Installazione PyInstaller...
".venv\Scripts\python.exe" -m pip install pyinstaller

echo Creazione eseguibile in corso (puo' richiedere qualche minuto)...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --windowed --onefile ^
    --name "PolliniSintomi" ^
    --collect-all customtkinter ^
    main.py

echo.
if exist "dist\PolliniSintomi.exe" (
    echo FATTO! Eseguibile creato in: dist\PolliniSintomi.exe
) else (
    echo ATTENZIONE: build non riuscita, controlla i messaggi sopra.
)
echo.
pause
