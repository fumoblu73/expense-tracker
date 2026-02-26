"""
Backup Manager
Gestione backup e ripristino completo del database
"""

import pandas as pd
import zipfile
import json
from io import BytesIO
from datetime import datetime
import streamlit as st


def create_full_backup(db):
    """
    Crea un backup completo in formato ZIP

    Args:
        db: istanza di ExpenseDB

    Returns:
        BytesIO: Buffer contenente il file ZIP
    """
    conn = db._get_conn()

    # Crea buffer in memoria per il ZIP
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Esporta transazioni
        transactions = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
        transactions_csv = transactions.to_csv(index=False)
        zip_file.writestr('transactions.csv', transactions_csv)

        # 2. Esporta categorie con budget
        categories = pd.read_sql_query("SELECT * FROM categories", conn)
        categories_csv = categories.to_csv(index=False)
        zip_file.writestr('categories.csv', categories_csv)

        # 3. Esporta merchant appresi
        try:
            merchants = pd.read_sql_query("SELECT * FROM merchant_categories", conn)
            merchants_csv = merchants.to_csv(index=False)
            zip_file.writestr('merchants.csv', merchants_csv)
        except Exception:
            # Se la tabella non esiste ancora, crea file vuoto
            zip_file.writestr('merchants.csv', 'merchant,category,usage_count,last_used\n')

        # 4. Esporta spese ricorrenti (se la tabella esiste)
        try:
            recurring = pd.read_sql_query("SELECT * FROM recurring_expenses", conn)
            recurring_csv = recurring.to_csv(index=False)
            zip_file.writestr('recurring_expenses.csv', recurring_csv)
        except Exception:
            # Tabella non esiste ancora
            pass

        # 5. Crea metadata
        metadata = {
            'backup_date': datetime.now().isoformat(),
            'app_version': '2.0.0',
            'transaction_count': len(transactions),
            'category_count': len(categories),
            'format_version': '1.0'
        }
        zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))

    conn.close()

    # Riposiziona il buffer all'inizio
    zip_buffer.seek(0)
    return zip_buffer


def extract_backup_info(uploaded_zip):
    """
    Estrae informazioni dal file di backup senza importarlo

    Returns:
        dict: Informazioni sul backup
    """
    try:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_file:
            # Leggi metadata
            if 'metadata.json' in zip_file.namelist():
                metadata = json.loads(zip_file.read('metadata.json'))
            else:
                metadata = {'backup_date': 'Sconosciuta', 'format_version': 'legacy'}

            # Conta elementi
            info = {
                'metadata': metadata,
                'files': {}
            }

            # Conta transazioni
            if 'transactions.csv' in zip_file.namelist():
                trans_data = zip_file.read('transactions.csv').decode('utf-8')
                trans_df = pd.read_csv(BytesIO(trans_data.encode()))
                info['files']['transactions'] = len(trans_df)

            # Conta categorie
            if 'categories.csv' in zip_file.namelist():
                cat_data = zip_file.read('categories.csv').decode('utf-8')
                cat_df = pd.read_csv(BytesIO(cat_data.encode()))
                info['files']['categories'] = len(cat_df)

            # Conta merchant
            if 'merchants.csv' in zip_file.namelist():
                merch_data = zip_file.read('merchants.csv').decode('utf-8')
                merch_df = pd.read_csv(BytesIO(merch_data.encode()))
                info['files']['merchants'] = len(merch_df)

            # Conta ricorrenti
            if 'recurring_expenses.csv' in zip_file.namelist():
                rec_data = zip_file.read('recurring_expenses.csv').decode('utf-8')
                rec_df = pd.read_csv(BytesIO(rec_data.encode()))
                info['files']['recurring'] = len(rec_df)

            return info

    except Exception as e:
        st.error(f"Errore nella lettura del backup: {str(e)}")
        return None


def restore_backup(uploaded_zip, db, mode='replace'):
    """
    Ripristina il backup

    Args:
        uploaded_zip: File ZIP caricato
        db: istanza di ExpenseDB
        mode: 'replace' (sostituisce tutto) o 'merge' (aggiunge solo nuovi dati)

    Returns:
        dict: Statistiche sul ripristino
    """
    conn = db._get_conn()
    cursor = conn.cursor()
    stats = {'transactions': 0, 'categories': 0, 'merchants': 0, 'recurring': 0}

    try:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_file:

            # MODALITÀ REPLACE: Cancella tutto prima
            if mode == 'replace':
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM categories")
                try:
                    cursor.execute("DELETE FROM merchant_categories")
                except Exception:
                    pass
                try:
                    cursor.execute("DELETE FROM recurring_expenses")
                except Exception:
                    pass
                conn.commit()

            # 1. Ripristina transazioni
            if 'transactions.csv' in zip_file.namelist():
                trans_data = zip_file.read('transactions.csv').decode('utf-8')
                trans_df = pd.read_csv(BytesIO(trans_data.encode()))

                if mode == 'merge':
                    # Evita duplicati
                    existing = pd.read_sql_query("SELECT date, description, amount FROM transactions", conn)
                    if len(existing) > 0:
                        existing['key'] = existing['date'].astype(str) + '|' + existing['description'] + '|' + existing['amount'].astype(str)
                        trans_df['key'] = trans_df['date'].astype(str) + '|' + trans_df['description'] + '|' + trans_df['amount'].astype(str)
                        trans_df = trans_df[~trans_df['key'].isin(existing['key'])].drop(columns=['key'])

                if len(trans_df) > 0:
                    # Rimuovi colonna id se presente (auto-generata dal DB)
                    trans_df = trans_df.drop(columns=['id'], errors='ignore')
                    trans_df.to_sql('transactions', db.engine, if_exists='append', index=False)
                    stats['transactions'] = len(trans_df)

            # 2. Ripristina categorie
            if 'categories.csv' in zip_file.namelist():
                cat_data = zip_file.read('categories.csv').decode('utf-8')
                cat_df = pd.read_csv(BytesIO(cat_data.encode()))

                if mode == 'merge':
                    # Aggiorna solo se non esistono
                    existing_cats = pd.read_sql_query("SELECT name FROM categories", conn)
                    cat_df = cat_df[~cat_df['name'].isin(existing_cats['name'])]

                if len(cat_df) > 0:
                    cat_df = cat_df.drop(columns=['id'], errors='ignore')
                    cat_df.to_sql('categories', db.engine, if_exists='append', index=False)
                    stats['categories'] = len(cat_df)

            # 3. Ripristina merchant
            if 'merchants.csv' in zip_file.namelist():
                merch_data = zip_file.read('merchants.csv').decode('utf-8')
                merch_df = pd.read_csv(BytesIO(merch_data.encode()))

                if len(merch_df) > 0 and 'merchant' in merch_df.columns:
                    if mode == 'merge':
                        try:
                            existing_merch = pd.read_sql_query("SELECT merchant FROM merchant_categories", conn)
                            merch_df = merch_df[~merch_df['merchant'].isin(existing_merch['merchant'])]
                        except Exception:
                            pass

                    if len(merch_df) > 0:
                        merch_df = merch_df.drop(columns=['id'], errors='ignore')
                        merch_df.to_sql('merchant_categories', db.engine, if_exists='append', index=False)
                        stats['merchants'] = len(merch_df)

            # 4. Ripristina ricorrenti
            if 'recurring_expenses.csv' in zip_file.namelist():
                rec_data = zip_file.read('recurring_expenses.csv').decode('utf-8')
                rec_df = pd.read_csv(BytesIO(rec_data.encode()))

                if len(rec_df) > 0:
                    if mode == 'merge':
                        try:
                            existing_rec = pd.read_sql_query("SELECT name FROM recurring_expenses", conn)
                            rec_df = rec_df[~rec_df['name'].isin(existing_rec['name'])]
                        except Exception:
                            pass

                    if len(rec_df) > 0:
                        rec_df = rec_df.drop(columns=['id'], errors='ignore')
                        rec_df.to_sql('recurring_expenses', db.engine, if_exists='append', index=False)
                        stats['recurring'] = len(rec_df)

        return stats

    except Exception as e:
        conn.rollback()
        st.error(f"Errore nel ripristino: {str(e)}")
        return None
    finally:
        conn.close()


def get_backup_filename():
    """Genera nome file backup con timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"backup_spese_{timestamp}.zip"
