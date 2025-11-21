@echo off
echo ========================================
echo   Caricamento su GitHub
echo ========================================
echo.

REM Controlla se git e installato
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git non trovato!
    echo.
    echo Scarica e installa Git da: https://git-scm.com/download/win
    echo.
    echo Dopo l'installazione, riavvia questo script.
    pause
    exit /b 1
)

echo Git trovato!
echo.

REM Inizializza repository
echo Inizializzo repository Git...
git init

REM Aggiungi tutti i file
echo Aggiunto tutti i file...
git add .

REM Commit
echo Creo commit iniziale...
git commit -m "Prima versione Family Expense Tracker"

echo.
echo ========================================
echo   PROSSIMI PASSI:
echo ========================================
echo.
echo 1. Vai su https://github.com/new
echo 2. Nome repository: expense-tracker
echo 3. Scegli: Private (per tenere i dati privati)
echo 4. NON selezionare "Initialize with README"
echo 5. Clicca "Create repository"
echo.
echo 6. Copia il comando che GitHub ti mostra:
echo    git remote add origin https://github.com/TUO-USERNAME/expense-tracker.git
echo.
echo 7. Incollalo qui sotto e premi INVIO:
echo.

set /p remote="Incolla comando git remote add origin: "

REM Esegui il comando
%remote%

REM Push
echo.
echo Caricamento su GitHub in corso...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo   COMPLETATO!
echo ========================================
echo.
echo Il tuo codice e ora su GitHub!
echo.
echo PROSSIMO PASSO: Deploy su Streamlit Cloud
echo Leggi il file: DEPLOY_STREAMLIT.md
echo.
pause
