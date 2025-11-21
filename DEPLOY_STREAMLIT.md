# 🚀 Guida Deploy su Streamlit Cloud

## La tua app sarà accessibile da qualsiasi dispositivo, ovunque!

---

## 📋 Cosa Serve

✅ Account GitHub (gratuito)
✅ Account Streamlit (gratuito)
✅ 10 minuti di tempo

**Costo totale: €0** - Tutto gratuito per sempre!

---

## 🎯 METODO 1: Deploy Manuale (PIÙ SEMPLICE)

### PASSO 1: Crea Account GitHub

1. Vai su: **https://github.com/signup**
2. Crea account con la tua email
3. Verifica l'email
4. Accedi a GitHub

### PASSO 2: Carica il Progetto

**Opzione A - Interfaccia Web (CONSIGLIATA per principianti)**:

1. Vai su: **https://github.com/new**

2. Compila:
   - **Repository name**: `expense-tracker`
   - **Description**: `App gestione spese familiari`
   - **Visibilità**: ✅ **Private** (per mantenere i dati privati)
   - ❌ NON selezionare "Add a README"

3. Clicca **"Create repository"**

4. Nella pagina che si apre, clicca su:
   **"uploading an existing file"** (link in alto)

5. **Trascina TUTTI i file** dalla cartella `C:\Temp\expense-tracker` nella pagina:
   - app.py
   - requirements.txt
   - README.md
   - GUIDA_RAPIDA.md
   - INIZIA_QUI.md
   - esempio_template.csv
   - .gitignore
   - Cartella database/ (con i suoi file)
   - Cartella utils/ (con i suoi file)
   - Cartella .streamlit/ (con i suoi file)

6. Nella casella "Commit changes":
   - Scrivi: `Prima versione`
   - Clicca **"Commit changes"**

**Opzione B - Con GitHub Desktop (se preferisci un'app)**:

1. Scarica **GitHub Desktop**: https://desktop.github.com/
2. Installa e accedi con il tuo account GitHub
3. File → Add Local Repository
4. Seleziona: `C:\Temp\expense-tracker`
5. Clicca "Publish Repository"
6. ✅ Keep this code private
7. Publish!

### PASSO 3: Deploy su Streamlit Cloud

1. Vai su: **https://share.streamlit.io/signup**

2. Clicca **"Continue with GitHub"**

3. Autorizza Streamlit ad accedere ai tuoi repository

4. Una volta loggato, clicca **"New app"** (in alto a destra)

5. Compila il form:
   - **Repository**: Seleziona `TUO-USERNAME/expense-tracker`
   - **Branch**: `main`
   - **Main file path**: `app.py`

6. Clicca **"Deploy!"**

7. **Aspetta 2-3 minuti** mentre Streamlit installa tutto

8. 🎉 **FATTO!** La tua app è online!

### PASSO 4: Ottieni il Tuo URL

Streamlit ti assegnerà un URL tipo:
```
https://tuo-username-expense-tracker-app-abc123.streamlit.app
```

**Salva questo URL!** È il link alla tua app.

---

## 🎯 METODO 2: Deploy con Script (Per utenti avanzati)

Se hai Git installato:

1. Apri il prompt dei comandi in `C:\Temp\expense-tracker`

2. Esegui:
```bash
# Se Git NON è installato, scaricalo da: https://git-scm.com/download/win

git init
git add .
git commit -m "Prima versione Family Expense Tracker"
```

3. Vai su https://github.com/new e crea il repository

4. Esegui (sostituisci TUO-USERNAME):
```bash
git remote add origin https://github.com/TUO-USERNAME/expense-tracker.git
git branch -M main
git push -u origin main
```

5. Poi segui il PASSO 3 del Metodo 1

---

## ⚙️ Configurare i Secrets (Email - Opzionale)

Se vuoi ricevere email dall'app:

1. Nel dashboard di Streamlit Cloud, apri la tua app

2. Clicca sull'icona **⚙️ Settings** (in basso a destra)

3. Vai su **"Secrets"**

4. Incolla questo (sostituisci con i tuoi dati):
```toml
[email]
sender = "tua-email@gmail.com"
password = "password-app-gmail"
```

5. Clicca **"Save"**

**Come ottenere la password app Gmail:**
1. Vai su https://myaccount.google.com
2. Sicurezza → Verifica in due passaggi (attivala)
3. Sicurezza → Password per le app
4. Genera password per "Posta"
5. Copia la password di 16 caratteri

---

## 🎉 La Tua App è Online!

### Cosa puoi fare ora:

✅ **Accedi da ovunque**
   - Smartphone
   - Tablet
   - Computer (casa, ufficio)
   - Qualsiasi browser

✅ **Condividi con la famiglia**
   - Invia il link ai familiari
   - Tutti possono vedere le spese
   - (Se vuoi login separati, contattami)

✅ **Sempre aggiornata**
   - I dati si salvano automaticamente
   - Backup su cloud
   - Zero manutenzione

---

## 📱 Usare l'App dal Telefono

### Come "App" sul telefono:

**iPhone/iPad:**
1. Apri Safari
2. Vai al tuo URL Streamlit
3. Clicca su "Condividi" (icona ↑)
4. Scorri e clicca "Aggiungi a Home"
5. Ora hai l'icona come un'app!

**Android:**
1. Apri Chrome
2. Vai al tuo URL Streamlit
3. Menu (⋮) → "Aggiungi a Home"
4. Ora hai l'icona come un'app!

---

## 🔄 Aggiornare l'App

Se vuoi modificare qualcosa:

### Con GitHub Web:
1. Vai sul tuo repository GitHub
2. Clicca sul file da modificare
3. Clicca l'icona ✏️ (Edit)
4. Modifica
5. "Commit changes"
6. Streamlit aggiorna automaticamente in 1 minuto!

### Con GitHub Desktop:
1. Modifica i file localmente
2. GitHub Desktop → Commit
3. Push origin
4. Streamlit aggiorna automaticamente!

---

## 🐛 Problemi Comuni

### "App non si avvia"

**Errore**: `No module named ...`
- ✅ Verifica che `requirements.txt` sia stato caricato
- ✅ Controlla i log su Streamlit Cloud
- ✅ Clicca "Reboot app" nel menu

### "Database vuoto"

È normale! Il database parte vuoto al primo avvio.
- Vai su "📤 Carica Dati"
- Importa il tuo CSV
- I dati si salvano automaticamente

### "Email non funziona"

- ✅ Hai configurato i Secrets?
- ✅ Password app (non password Gmail normale)
- ✅ Verifica in due passaggi attiva su Gmail

### "App va lenta"

Con il piano gratuito di Streamlit Cloud:
- 1GB RAM
- 1GB storage
- Può dormire dopo inattività (si risveglia in 30 sec)

Per prestazioni migliori:
- Carica solo ultimi 12 mesi di dati
- Archivia dati vecchi

---

## 💰 Costi

### Piano Gratuito (Quello che userai):
- ✅ 1 app pubblica illimitata
- ✅ 3 app private
- ✅ 1GB storage
- ✅ Uptime 24/7
- ✅ **Costo: €0/mese**

### Se in futuro vuoi di più:
- Streamlit Cloud Team: $20/mese (5 app, 4GB RAM)
- Streamlit Cloud Business: $250/mese (uso aziendale)

**Ma il piano gratuito è più che sufficiente per uso familiare!**

---

## 🔒 Sicurezza

### I tuoi dati sono sicuri?

✅ **Repository privato** su GitHub
   - Solo tu puoi vedere il codice

✅ **Database su Streamlit Cloud**
   - Collegato al tuo account
   - Nessun altro può accedere

✅ **HTTPS automatico**
   - Comunicazioni criptate

✅ **Secrets criptati**
   - Password email protette

### Condividere l'app

**Attenzione**: Se condividi il link, chiunque lo abbia può accedere!

**Per proteggere:**
1. Mantieni privato il link
2. Oppure aggiungi autenticazione (avanzato)
3. Oppure condividi solo report/export

---

## 📊 Monitorare l'App

Nel dashboard Streamlit Cloud puoi vedere:
- ✅ Stato app (online/offline)
- ✅ Log in tempo reale
- ✅ Utilizzo risorse
- ✅ Versione deployed
- ✅ Ultimo deploy

---

## 🎓 Prossimi Passi Dopo il Deploy

### Subito:
1. ✅ Testa l'app dal telefono
2. ✅ Carica i primi dati
3. ✅ Salva il link nei preferiti

### Entro oggi:
1. ✅ Importa tutti i movimenti bancari
2. ✅ Configura categorie e budget
3. ✅ (Opzionale) Configura email

### Entro settimana:
1. ✅ Analizza prime statistiche
2. ✅ Condividi con famiglia (se vuoi)
3. ✅ Inizia a risparmiare! 💰

---

## 🌟 Vantaggi Deploy Cloud

### VS Locale:

| Caratteristica | Locale | Cloud |
|---------------|--------|-------|
| Accessibilità | Solo da quel PC | Da ovunque |
| Mobile | No | ✅ Sì |
| Backup | Manuale | ✅ Automatico |
| Aggiornamenti | Manuali | ✅ Automatici |
| Condivisione | Difficile | ✅ Facile |
| Manutenzione | Tua | ✅ Zero |
| Costo | €0 | €0 |

**Conviene sempre il cloud per questo tipo di app!**

---

## 📞 Help Rapido

### GitHub non funziona?
→ Segui il wizard su github.com
→ Oppure usa GitHub Desktop (più semplice)

### Streamlit non fa il deploy?
→ Controlla i log nella dashboard
→ Verifica che requirements.txt sia presente
→ Prova "Reboot app"

### App troppo lenta?
→ Normale al primo avvio (installa dipendenze)
→ Dopo 2-3 minuti diventa veloce
→ Se dorme, risveglio in 30 secondi

---

## 🎯 Checklist Deploy

Usa questa checklist:

- [ ] Account GitHub creato
- [ ] Repository expense-tracker creato
- [ ] Tutti i file caricati su GitHub
- [ ] Account Streamlit Cloud creato
- [ ] App deployed
- [ ] URL app salvato
- [ ] App testata da browser
- [ ] App testata da telefono
- [ ] (Opzionale) Email configurata
- [ ] Primi dati caricati
- [ ] Link condiviso con famiglia

---

## 🎉 CONGRATULAZIONI!

La tua app è online e accessibile da qualsiasi dispositivo!

### Il tuo link:
```
https://[tuo-username]-expense-tracker-app-[id].streamlit.app
```

### Salvalo nei preferiti:
- Browser computer
- Home screen telefono
- Condividi con la famiglia

---

## 💡 Tips Finali

**Per usare al meglio l'app cloud:**

1. **Carica dati regolarmente** - Ogni settimana/mese
2. **Usa da mobile** - Più comodo per check veloci
3. **Imposta budget realistici** - Basati sulla media storica
4. **Analizza i trend** - Identifica dove risparmiare
5. **Condividi i report** - Tieni la famiglia informata

---

**Buona gestione delle spese dal cloud! ☁️💰**

---

<div align="center">

### Hai bisogno di aiuto?

📖 Leggi: [README.md](README.md)
🚀 Riprova: Segui questa guida step-by-step
📧 Scrivi: [Apri issue su GitHub]

</div>
