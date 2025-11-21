#!/bin/bash

echo "========================================"
echo "  Family Expense Tracker"
echo "  Avvio applicazione..."
echo "========================================"
echo ""

# Verifica se Python è installato
if ! command -v python3 &> /dev/null
then
    echo "ERRORE: Python non trovato!"
    echo ""
    echo "Installa Python da: https://www.python.org/downloads/"
    echo "Oppure usa il package manager del tuo sistema:"
    echo "  - Mac: brew install python3"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo ""
    exit 1
fi

echo "Python trovato!"
echo ""

# Verifica se le dipendenze sono installate
python3 -c "import streamlit" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installazione dipendenze in corso..."
    echo "Questo potrebbe richiedere qualche minuto..."
    echo ""
    python3 -m pip install -r requirements.txt
    echo ""
    echo "Dipendenze installate!"
    echo ""
fi

echo "Avvio Family Expense Tracker..."
echo "L'applicazione si aprirà automaticamente nel browser"
echo ""
echo "Per chiudere l'app, premi CTRL+C in questa finestra"
echo ""

python3 -m streamlit run app.py
