# 🚀 Guida Rapida - Family Expense Tracker

## Avvio Immediato in 3 Passi

### 1️⃣ Installa Python

Se non hai Python installato:

1. Vai su [python.org/downloads](https://www.python.org/downloads/)
2. Scarica Python 3.10 o superiore
3. **IMPORTANTE**: Durante l'installazione, seleziona "Add Python to PATH"

### 2️⃣ Installa le Dipendenze

Apri il Terminale/Prompt dei Comandi nella cartella del progetto e digita:

**Windows:**
```bash
python -m pip install -r requirements.txt
```

**Mac/Linux:**
```bash
python3 -m pip install -r requirements.txt
```

### 3️⃣ Avvia l'App

**Windows:**
```bash
python -m streamlit run app.py
```

**Mac/Linux:**
```bash
python3 -m streamlit run app.py
```

L'app si aprirà automaticamente nel browser su `http://localhost:8501`

---

## 🎯 Primi Passi nell'App

### Passo 1: Scarica il CSV dalla Banca

Vai sul sito della tua banca e scarica l'estratto conto in formato CSV:

- **Intesa Sanpaolo**: Area Clienti → Conto Corrente → Movimenti → Esporta
- **UniCredit**: Banca via Internet → Conto → Movimenti → Scarica CSV
- **Banco BPM**: YouWeb → Conti → Movimenti → Esporta
- **Poste Italiane**: BancoPosta Online → Conto → Movimenti → Download

### Passo 2: Carica il File

1. Nell'app, clicca su **📤 Carica Dati** nella sidebar
2. Trascina il file CSV o clicca per selezionarlo
3. Verifica l'anteprima dei dati
4. Clicca **💾 Salva nel Database**

### Passo 3: Categorizza le Spese

1. Vai su **🏷️ Gestisci Categorie**
2. Nella tab **🔄 Ricategorizza**, assegna le categorie alle transazioni
3. Oppure usa la categorizzazione automatica durante il caricamento

### Passo 4: Imposta i Budget

1. Sempre in **🏷️ Gestisci Categorie**
2. Vai sulla tab **✏️ Modifica Budget**
3. Imposta il budget mensile per ogni categoria
4. Clicca 💾 per salvare

### Passo 5: Monitora!

1. Torna su **🏠 Dashboard**
2. Visualizza grafici, statistiche e alert
3. Controlla se stai rispettando i budget

---

## 📧 Configurare le Email (Opzionale)

### Ottieni Password App Gmail

1. Vai su [myaccount.google.com](https://myaccount.google.com)
2. Sicurezza → Verifica in due passaggi (attivala)
3. Sicurezza → Password per le app
4. Seleziona "Posta" → Genera
5. Copia la password di 16 caratteri

### Configura nell'App

1. Crea il file `.streamlit/secrets.toml`
2. Copia il contenuto da `.streamlit/secrets.toml.example`
3. Sostituisci con la tua email e password
4. Salva

Esempio:
```toml
[email]
sender = "mario.rossi@gmail.com"
password = "abcd efgh ijkl mnop"
```

### Testa

1. Vai su **⚙️ Impostazioni → Email**
2. Segui le istruzioni per il test
3. Invia email di prova

---

## ☁️ Pubblicare Online (Avanzato)

Vuoi accedere all'app dal telefono ovunque ti trovi?

### 1. Carica su GitHub

**Con GitHub Desktop (più semplice):**
1. Scarica [GitHub Desktop](https://desktop.github.com)
2. File → Add Local Repository → Seleziona `expense-tracker`
3. Publish Repository

**Con terminale:**
```bash
git init
git add .
git commit -m "First commit"
git remote add origin https://github.com/TUO-USERNAME/expense-tracker.git
git push -u origin main
```

### 2. Deploy su Streamlit Cloud

1. Vai su [streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign up con GitHub
3. New app → Seleziona il tuo repository
4. Deploy!

Avrai un URL tipo: `https://tuo-nome-expense-tracker.streamlit.app`

---

## ❓ Problemi Comuni

### "streamlit: command not found"

**Soluzione**: Usa il comando completo:
```bash
python -m streamlit run app.py
```

### "No module named 'streamlit'"

**Soluzione**: Installa le dipendenze:
```bash
pip install -r requirements.txt
```

### Il CSV non viene riconosciuto

**Soluzione**:
- Verifica che abbia le colonne: Data, Descrizione, Importo
- Scarica il template di esempio dall'app
- Prova con un altro formato di export dalla banca

### L'app va lenta

**Soluzione**:
- Normale con molti dati (>10.000 transazioni)
- Considera di archiviare i dati più vecchi
- Usa filtri per periodo specifico nei report

---

## 📞 Serve Aiuto?

1. Leggi il [README completo](README.md)
2. Controlla la sezione "Risoluzione Problemi"
3. Cerca su Google l'errore specifico
4. Contatta il supporto

---

## 🎉 Buon Tracciamento delle Spese!

Ricorda:
- ✅ Carica i dati regolarmente (ogni settimana/mese)
- ✅ Categorizza le spese appena caricate
- ✅ Controlla la dashboard per rimanere nei budget
- ✅ Usa i report per identificare dove risparmiare

**Fatto con ❤️ per le famiglie italiane**
