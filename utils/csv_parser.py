"""
CSV Parser per file bancari
Supporta diversi formati di CSV da banche italiane
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from utils.formatters import format_currency_ita


def parse_bank_csv(uploaded_file, date_format='auto'):
    """
    Parse e valida file CSV o Excel bancario

    Args:
        uploaded_file: File caricato da Streamlit (CSV, XLS, XLSX)
        date_format: Formato data ('auto', 'DD/MM/YYYY', 'YYYY-MM-DD', etc.)

    Returns:
        DataFrame con colonne standardizzate o None in caso di errore
    """
    try:
        # Rileva il tipo di file dal nome
        file_name = uploaded_file.name.lower()

        # Leggi file Excel (XLS o XLSX)
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            try:
                # Prima prova con xlrd (per .xls vecchio formato)
                df = pd.read_excel(uploaded_file, engine='xlrd')
            except:
                uploaded_file.seek(0)
                try:
                    # Poi prova con openpyxl (per .xlsx moderni)
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                except:
                    uploaded_file.seek(0)
                    try:
                        # Potrebbe essere un HTML mascherato da .xls (comune per banche italiane)
                        df = pd.read_html(uploaded_file, encoding='utf-8')[0]
                    except:
                        uploaded_file.seek(0)
                        try:
                            # Potrebbe essere un CSV con estensione .xls
                            df = pd.read_csv(uploaded_file, sep=';', encoding='latin-1')
                        except:
                            uploaded_file.seek(0)
                            # Ultimo tentativo con encoding diverso
                            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

        # Leggi file CSV con diversi encoding
        else:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                except:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='iso-8859-1', sep=';')

        # Pulisci i nomi delle colonne (rimuovi spazi extra)
        df.columns = df.columns.str.strip()

        # Auto-detect colonne
        column_mapping = detect_columns(df)

        # Valida che ci siano le colonne necessarie
        if not all(k in column_mapping for k in ['date', 'amount', 'description']):
            st.error("⚠️ Il file non contiene tutte le colonne necessarie")
            st.info("📋 **Colonne trovate:**")
            for col in df.columns.tolist():
                st.write(f"  - `{col}`")
            st.info("📋 **Mapping rilevato:**")
            for key, val in column_mapping.items():
                st.write(f"  - {key} → `{val}`")
            st.warning("💡 Assicurati che il file contenga almeno: Data, Importo, Descrizione")
            return None

        # Standardizza nomi colonne usando il mapping rilevato
        # Crea reverse mapping per rinominare correttamente
        reverse_mapping = {v: k for k, v in column_mapping.items()}
        df = df.rename(columns=reverse_mapping)

        # Seleziona solo le colonne che ci servono
        columns_to_keep = ['date', 'description', 'amount']
        if 'notes' in df.columns:
            columns_to_keep.append('notes')

        df = df[columns_to_keep].copy()

        # Converti data
        df['date'] = parse_dates(df['date'], date_format)

        # Converti importo in numero (mantiene il segno)
        df['amount'] = parse_amounts(df['amount'])

        # Rimuovi righe con valori nulli critici
        df = df.dropna(subset=['date', 'amount'])

        # Salva il segno originale per categorizzazione Entrate/Uscite
        df['amount_sign'] = df['amount'].apply(lambda x: 'income' if x > 0 else 'expense')

        # Converti importi in valore assoluto (il database salva tutto positivo)
        df['amount'] = df['amount'].abs()

        # Aggiungi colonna merchant (vuota per ora, verrà popolata dall'app)
        df['merchant'] = ''

        # Aggiungi colonna categoria (inizialmente 'Non Categorizzato')
        df['category'] = 'Non Categorizzato'

        # Aggiungi colonna note se non esiste
        if 'notes' not in df.columns:
            df['notes'] = ''

        # Converti date in formato stringa per SQLite
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        # Ordina per data (più recenti prima)
        df = df.sort_values('date', ascending=False)

        return df

    except Exception as e:
        st.error(f"❌ Errore nel parsing del CSV: {str(e)}")
        return None


def detect_columns(df):
    """
    Auto-detect colonne da vari formati bancari italiani

    Formati supportati:
    - Intesa Sanpaolo
    - UniCredit
    - Banco BPM
    - Poste Italiane
    - Altri formati standard
    """
    mapping = {}
    columns_lower = {col: col.lower() for col in df.columns}

    # Cerca colonna data
    # PRIORITÀ: "Data Valuta" è più affidabile di "Data Contabile"
    date_keywords = [
        'data valuta',  # PRIORITÀ 1: Data effettiva transazione
        'data contabile',  # PRIORITÀ 2: Data registrazione contabile
        'data operazione',  # PRIORITÀ 3: Data operazione
        'data', 'date', 'fecha', 'datum'  # Generici
    ]
    for keyword in date_keywords:
        for col, col_lower in columns_lower.items():
            if keyword in col_lower:
                mapping['date'] = col
                break
        if 'date' in mapping:  # Se trovata, esci
            break

    # Cerca colonna importo
    amount_keywords = [
        'importo', 'amount', 'ammontare', 'valore', 'entrate', 'uscite',
        'dare', 'avere', 'movimento', 'somma'
    ]
    for col, col_lower in columns_lower.items():
        if any(keyword in col_lower for keyword in amount_keywords):
            mapping['amount'] = col
            break

    # Cerca colonna descrizione
    description_keywords = [
        'descrizione', 'description', 'desc', 'dettagli', 'details',
        'causale', 'tipo operazione', 'operazione'
    ]
    for col, col_lower in columns_lower.items():
        if any(keyword in col_lower for keyword in description_keywords):
            mapping['description'] = col
            break

    # Cerca colonna note (opzionale)
    notes_keywords = ['note', 'notes', 'memo', 'commento']
    for col, col_lower in columns_lower.items():
        if any(keyword in col_lower for keyword in notes_keywords):
            mapping['notes'] = col
            break

    return mapping


def parse_dates(date_series, date_format='auto'):
    """Parse date con vari formati"""
    if date_format == 'auto':
        # Prova diversi formati comuni in Italia
        formats_to_try = [
            '%d/%m/%Y',  # 31/12/2024
            '%Y-%m-%d',  # 2024-12-31
            '%d-%m-%Y',  # 31-12-2024
            '%d.%m.%Y',  # 31.12.2024
            '%Y/%m/%d',  # 2024/12/31
        ]

        for fmt in formats_to_try:
            try:
                return pd.to_datetime(date_series, format=fmt, errors='coerce')
            except:
                continue

        # Se nessun formato funziona, prova inferenza automatica
        return pd.to_datetime(date_series, errors='coerce', dayfirst=True)
    else:
        return pd.to_datetime(date_series, format=date_format, errors='coerce')


def parse_amounts(amount_series):
    """
    Parse importi gestendo formati italiani

    IMPORTANTE: Gestisce correttamente valori con virgola decimale italiana
    Esempio: "-19,99" → -19.99 (NON -1999!)
    """
    # PRIMA converti TUTTO in stringa, anche se già numerico
    # Questo è necessario perché pandas/HTML potrebbero aver già letto i valori
    amount_series = amount_series.astype(str)

    # Rimuovi spazi
    amount_series = amount_series.str.strip()

    def convert_italian_amount(val):
        """
        Converte importo italiano in float

        Casi gestiti:
        - "-19,99" → -19.99
        - "-1.234,56" → -1234.56
        - "18,30" → 18.30
        - "-19.99" (già formato US) → -19.99
        - nan, None → nan
        """
        val = str(val).strip()

        # Gestisci valori nulli
        if val in ['nan', 'None', '', 'NaN']:
            return None

        # Rimuovi simboli valuta
        val = val.replace('€', '').replace('EUR', '').strip()

        # Caso 1: Formato italiano con virgola (es: "-19,99" o "-1.234,56")
        if ',' in val:
            # La virgola è SEMPRE il separatore decimale in formato italiano
            # Il punto (se presente) è SEMPRE il separatore migliaia
            val = val.replace('.', '')  # Rimuovi separatori migliaia
            val = val.replace(',', '.')  # Virgola diventa punto decimale

        # Caso 2: Già in formato corretto (punto decimale) o solo numero intero
        # Non fare nulla, mantieni com'è

        return val

    amount_series = amount_series.apply(convert_italian_amount)

    # Converti in numero MANTENENDO IL SEGNO (negativo = spesa, positivo = entrata)
    return pd.to_numeric(amount_series, errors='coerce')


def validate_csv_preview(df, num_rows=5):
    """Mostra anteprima del CSV parsato per validazione"""
    if df is None or len(df) == 0:
        return False

    st.success(f"✅ File caricato con successo! Trovate {len(df)} transazioni")

    # Statistiche rapide
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale Transazioni", len(df))
    with col2:
        st.metric("Totale Importo", format_currency_ita(df['amount'].sum()))
    with col3:
        if len(df) > 0:
            date_range = f"{df['date'].min()} - {df['date'].max()}"
            st.metric("Periodo", "📅")
            st.caption(date_range)

    # Mostra anteprima
    st.subheader("👀 Anteprima dati")
    st.dataframe(
        df.head(num_rows),
        use_container_width=True,
        hide_index=True
    )

    return True


def get_sample_csv_template():
    """Restituisce un template CSV di esempio"""
    sample_data = {
        'Data': ['01/01/2024', '02/01/2024', '03/01/2024'],
        'Descrizione': ['Spesa supermercato', 'Rifornimento benzina', 'Ristorante'],
        'Importo': ['45,50', '60,00', '35,80']
    }
    return pd.DataFrame(sample_data)
