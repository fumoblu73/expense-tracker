# 💰 Family Expense Tracker

**App web gratuita per la gestione e il monitoraggio delle spese familiari**

Semplice, intuitiva e ottimizzata per dispositivi mobili. Accessibile ovunque, da qualsiasi dispositivo.

---

## 🌟 Caratteristiche Principali

- ✅ **Importazione CSV automatica** - Carica i file dalla tua banca in pochi click
- ✅ **Categorizzazione intelligente** - Assegna categorie manualmente o automaticamente
- ✅ **Budget mensili** - Imposta budget per categoria e ricevi alert
- ✅ **Dashboard interattiva** - Grafici e statistiche in tempo reale
- ✅ **Previsioni** - Anticipa le spese future con analisi predittive
- ✅ **Report dettagliati** - Analizza le tue abitudini di spesa
- ✅ **Notifiche email** - Ricevi report e alert via email
- ✅ **100% Mobile-friendly** - Perfetto per smartphone e tablet
- ✅ **Completamente gratuito** - Nessun costo nascosto

---

## 📱 Screenshot

```
┌─────────────────────────────────────┐
│  💰 Family Expense Tracker          │
│                                     │
│  📊 Dashboard                       │
│  ┌──────────┬──────────┬─────────┐ │
│  │ Spesa    │ Trans.   │ Media   │ │
│  │ €1,234   │ 42       │ €41.15  │ │
│  └──────────┴──────────┴─────────┘ │
│                                     │
│  [Grafico Spese Mensili]            │
│  [Grafico Categorie]                │
│                                     │
└─────────────────────────────────────┘
```

---

## 🚀 Guida Rapida all'Avvio

### Requisiti

- **Python 3.10 o superiore** - [Scarica qui](https://www.python.org/downloads/)
- **Account Google** (per deploy cloud e email - opzionale)
- **Account GitHub** (per pubblicare online - opzionale)

### Installazione Locale (5 minuti)

1. **Scarica il progetto**
   ```bash
   # Se hai git installato
   git clone <url-repository>
   cd expense-tracker

   # OPPURE scarica e decomprimi il file ZIP
   ```

2. **Installa Python** (se non ce l'hai)
   - Vai su [python.org](https://www.python.org/downloads/)
   - Scarica Python 3.10 o superiore
   - Durante l'installazione, **seleziona "Add Python to PATH"**

3. **Installa le dipendenze**
   ```bash
   # Windows
   python -m pip install -r requirements.txt

   # Mac/Linux
   python3 -m pip install -r requirements.txt
   ```

4. **Avvia l'applicazione**
   ```bash
   # Windows
   python -m streamlit run app.py

   # Mac/Linux
   python3 -m streamlit run app.py
   ```

5. **Apri il browser**
   - L'app si aprirà automaticamente su `http://localhost:8501`
   - Se non si apre, copia l'URL dalla console

---

## 📖 Come Usare l'App

### 1️⃣ Carica i Dati Bancari

1. Vai sulla sezione **📤 Carica Dati**
2. Scarica il file CSV dalla tua banca:
   - **Intesa Sanpaolo**: Area Clienti → Movimenti → Esporta CSV
   - **UniCredit**: Banca via Internet → Movimenti → Scarica
   - **Poste Italiane**: BancoPosta Online → Movimenti → Esporta
   - *Altre banche*: Cerca "Esporta movimenti" o "Download CSV"
3. Trascina il file CSV nell'app (o clicca per selezionarlo)
4. Verifica l'anteprima dei dati
5. Clicca **💾 Salva nel Database**

### 2️⃣ Gestisci le Categorie

1. Vai su **🏷️ Gestisci Categorie**
2. L'app include categorie predefinite:
   - 🛒 Alimentari
   - 🚗 Trasporti
   - 💡 Utenze
   - 🍽️ Ristoranti
   - 🛍️ Shopping
   - ⚕️ Salute
   - 🎬 Svago
   - 🏠 Casa
   - 📦 Altro
3. **Aggiungi categorie personalizzate** se necessario
4. **Imposta i budget mensili** per ogni categoria
5. **Ricategorizza** le transazioni non categorizzate

### 3️⃣ Monitora le Spese

1. Vai su **🏠 Dashboard** per vedere:
   - Spesa totale del mese corrente
   - Numero di transazioni
   - Media per transazione
   - Media giornaliera
2. **Alert automatici** quando ti avvicini al budget
3. **Grafici interattivi**:
   - Andamento mensile
   - Distribuzione per categoria
   - Budget vs Spesa effettiva
   - Trend giornaliero

### 4️⃣ Analizza e Prevedi

1. **📊 Report & Analisi**:
   - Report mensile dettagliato
   - Confronto con mese/anno precedente
   - Analisi trend per categoria
   - Export CSV per ulteriori elaborazioni

2. **🔮 Previsioni**:
   - Previsione spese future (basata su media mobile)
   - Trend per categoria
   - Raccomandazioni personalizzate

### 5️⃣ Ricevi Report via Email

1. Vai su **⚙️ Impostazioni → Email**
2. Configura Gmail (vedi sezione Email qui sotto)
3. Torna su **📊 Report & Analisi → Invia Report**
4. Inserisci l'email destinatario
5. Clicca **📧 Invia Report**

---

## 📧 Configurazione Email (Opzionale)

Per ricevere report automatici via email:

### 1. Crea Password App Gmail

1. Vai su [Google Account](https://myaccount.google.com/)
2. Seleziona **Sicurezza** nel menu laterale
3. Attiva **Verifica in due passaggi** (se non è già attiva)
4. Torna su Sicurezza → In fondo trovi **Password per le app**
5. Clicca su **Password per le app**
6. Seleziona:
   - App: **Posta**
   - Dispositivo: **Windows/Mac** (il tuo computer)
7. Clicca **Genera**
8. **Copia la password di 16 caratteri** (apparirà solo una volta!)

### 2. Configura l'App

1. Nella cartella `expense-tracker`, crea il file `.streamlit/secrets.toml`
2. Aggiungi queste righe (sostituendo con i tuoi dati):

```toml
[email]
sender = "tua-email@gmail.com"
password = "abcd efgh ijkl mnop"
```

3. Salva il file
4. **IMPORTANTE**: NON condividere mai questo file con nessuno!

### 3. Testa l'Email

1. Vai su **⚙️ Impostazioni → Email → Test Configurazione Email**
2. Inserisci una email di test
3. Clicca **Invia Email di Test**
4. Verifica di aver ricevuto l'email

---

## ☁️ Pubblicare Online (Deploy Cloud Gratuito)

Vuoi accedere all'app da ovunque? Pubblicala gratis su Streamlit Cloud!

### Prerequisiti

1. Account GitHub (gratuito) - [Iscriviti qui](https://github.com/signup)
2. Account Streamlit (gratuito) - [Iscriviti qui](https://streamlit.io/cloud)

### Passaggi

#### 1. Carica il Codice su GitHub

**Opzione A - Con GitHub Desktop (più semplice)**:

1. Scarica [GitHub Desktop](https://desktop.github.com/)
2. Installa e accedi con il tuo account GitHub
3. File → Add Local Repository → Seleziona la cartella `expense-tracker`
4. Publish Repository → ✅ Keep this code private (se vuoi mantenerlo privato)
5. Publish!

**Opzione B - Con Git da terminale**:

```bash
cd expense-tracker
git init
git add .
git commit -m "Prima versione Family Expense Tracker"

# Crea un repository su github.com e poi:
git remote add origin https://github.com/TUO-USERNAME/expense-tracker.git
git push -u origin main
```

#### 2. Deploy su Streamlit Cloud

1. Vai su [streamlit.io/cloud](https://streamlit.io/cloud)
2. Clicca **Sign up with GitHub**
3. Autorizza Streamlit ad accedere ai tuoi repository
4. Clicca **New app**
5. Seleziona:
   - **Repository**: `TUO-USERNAME/expense-tracker`
   - **Branch**: `main`
   - **Main file path**: `app.py`
6. Clicca **Deploy!**

#### 3. Configura i Secrets (Email)

Se hai configurato l'email:

1. Nel dashboard di Streamlit Cloud, apri la tua app
2. Clicca su **⚙️ Settings** in basso a destra
3. Vai su **Secrets**
4. Copia il contenuto del tuo file `.streamlit/secrets.toml`
5. Incolla e salva

#### 4. Condividi l'App!

La tua app sarà disponibile su un URL tipo:
```
https://tuo-username-expense-tracker-app-xyz123.streamlit.app
```

Puoi condividere questo link con la tua famiglia!

---

## 📊 Formato CSV Supportato

L'app supporta CSV con queste colonne (i nomi possono variare):

| Colonna | Nomi Accettati | Esempio |
|---------|----------------|---------|
| **Data** | Data, Date, Data Operazione, Data Valuta | 01/01/2024 |
| **Descrizione** | Descrizione, Description, Causale, Dettagli | Spesa supermercato |
| **Importo** | Importo, Amount, Valore, Entrate, Uscite | 45,50 |
| **Note** (opzionale) | Note, Notes, Memo | Settimanale |

### Formati Data Supportati
- `31/12/2024` (formato italiano)
- `2024-12-31` (formato ISO)
- `31-12-2024`
- `31.12.2024`

### Formati Importo Supportati
- `1.234,56` (formato italiano)
- `1234.56` (formato internazionale)
- `€ 1.234,56`
- `1.234,56 EUR`

---

## 🗂️ Struttura del Progetto

```
expense-tracker/
│
├── app.py                      # App principale Streamlit
├── requirements.txt            # Dipendenze Python
├── README.md                   # Questa documentazione
│
├── .streamlit/
│   ├── config.toml            # Configurazione Streamlit
│   └── secrets.toml           # Credenziali email (NON committare!)
│
├── database/
│   └── db_manager.py          # Gestione database SQLite
│
├── utils/
│   ├── csv_parser.py          # Parsing CSV bancari
│   ├── visualizations.py      # Grafici Plotly
│   ├── budget_alerts.py       # Sistema alert budget
│   ├── forecasting.py         # Previsioni e statistiche
│   └── email_sender.py        # Invio email
│
└── data/
    └── expenses.db            # Database SQLite (creato automaticamente)
```

---

## 🐛 Risoluzione Problemi

### L'app non si avvia

**Errore**: `streamlit: command not found`
- **Soluzione**: Python non è nel PATH. Usa `python -m streamlit run app.py`

**Errore**: `No module named 'streamlit'`
- **Soluzione**: Installa le dipendenze: `pip install -r requirements.txt`

### Il CSV non viene caricato

**Problema**: "Colonne mancanti"
- **Soluzione**: Verifica che il CSV abbia almeno: Data, Descrizione, Importo
- Apri il CSV con Excel/Calc e controlla i nomi delle colonne
- Scarica il template di esempio dall'app

**Problema**: "Errore parsing date"
- **Soluzione**: Verifica il formato data. L'app supporta DD/MM/YYYY e YYYY-MM-DD

### Email non funziona

**Errore**: "Configurazione email mancante"
- **Soluzione**: Crea il file `.streamlit/secrets.toml` con le credenziali Gmail

**Errore**: "Authentication failed"
- **Soluzione**:
  - Usa una Password App, NON la password Gmail normale
  - Verifica che la Verifica in Due Passaggi sia attiva
  - Controlla di non avere spazi extra nel file secrets.toml

### Il database è corrotto

**Soluzione**:
1. Vai su **⚙️ Impostazioni → Database**
2. Scarica un backup CSV
3. Elimina il file `data/expenses.db`
4. Riavvia l'app (creerà un nuovo database vuoto)
5. Ricarica i dati dal backup CSV

---

## 💡 Suggerimenti e Best Practices

### Per Ottenere il Massimo dall'App

1. **Carica i dati regolarmente** - Meglio ogni settimana/mese
2. **Categorizza subito** - Più facile quando ricordi le spese
3. **Imposta budget realistici** - Inizia osservando la media del mese scorso
4. **Usa la categorizzazione automatica** - Velocizza il processo iniziale
5. **Controlla gli alert** - Ti aiutano a non sforare i budget
6. **Analizza i trend** - Identifica dove puoi risparmiare

### Risparmia Tempo

- **Crea categorie personalizzate** per le tue esigenze specifiche
- **Usa nomi descrittivi** per le categorie (es. "Spesa Settimanale" invece di "Food")
- **Esporta report mensili** per la contabilità domestica
- **Imposta reminder** nel calendario per caricare i dati ogni mese

### Privacy e Sicurezza

- ✅ Tutti i dati sono salvati localmente sul tuo computer/cloud
- ✅ Nessun dato viene inviato a server esterni (tranne le email che configuri)
- ✅ Il file `secrets.toml` NON deve mai essere condiviso
- ✅ Se pubblichi su GitHub, assicurati che `secrets.toml` sia in `.gitignore`

---

## 🎯 Roadmap Future Funzionalità

Possibili miglioramenti futuri:

- [ ] Multi-utente con login
- [ ] Sincronizzazione automatica con API bancarie
- [ ] App mobile nativa (Android/iOS)
- [ ] Grafici personalizzabili
- [ ] Export PDF dei report
- [ ] Integrazione con Google Sheets
- [ ] Budget annuali oltre che mensili
- [ ] Obiettivi di risparmio
- [ ] Categorizzazione AI avanzata
- [ ] Multi-valuta

---

## 🤝 Contribuire

Hai suggerimenti o vuoi contribuire?

1. Fai un Fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/nuova-funzione`)
3. Committa le modifiche (`git commit -m 'Aggiunta nuova funzione'`)
4. Push al branch (`git push origin feature/nuova-funzione`)
5. Apri una Pull Request

---

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT - sentiti libero di usarlo e modificarlo!

---

## 💬 Supporto

Hai problemi o domande?

- 📖 Leggi questa guida completa
- 💡 Controlla la sezione "Risoluzione Problemi"
- 📧 Contatta il supporto

---

## 🙏 Ringraziamenti

Realizzato con:
- [Streamlit](https://streamlit.io/) - Framework per app web in Python
- [Plotly](https://plotly.com/) - Libreria per grafici interattivi
- [Pandas](https://pandas.pydata.org/) - Analisi dati
- [SQLite](https://www.sqlite.org/) - Database embedded

---

<div align="center">

**Made with ❤️ for families**

⭐ Se ti piace il progetto, metti una stella su GitHub!

[🏠 Homepage](#) • [📖 Documentazione](#) • [🐛 Report Bug](#) • [💡 Richiedi Feature](#)

</div>
