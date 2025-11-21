@echo off
echo ========================================
echo   Family Expense Tracker
echo   Avvio applicazione...
echo ========================================
echo.

REM Verifica se Python e installato
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: Python non trovato!
    echo.
    echo Installa Python da: https://www.python.org/downloads/
    echo Assicurati di selezionare "Add Python to PATH" durante l'installazione
    echo.
    pause
    exit /b 1
)

echo Python trovato!
echo.

REM Verifica se le dipendenze sono installate
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installazione dipendenze in corso...
    echo Questo potrebbe richiedere qualche minuto...
    echo.
    python -m pip install -r requirements.txt
    echo.
    echo Dipendenze installate!
    echo.
)

echo Avvio Family Expense Tracker...
echo L'applicazione si aprira automaticamente nel browser
echo.
echo Per chiudere l'app, premi CTRL+C in questa finestra
echo.

python -m streamlit run app.py

pause
