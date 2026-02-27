"""
Database Manager per l'app di gestione spese familiari
Gestisce tutte le operazioni CRUD con PostgreSQL (Supabase)

Version: 3.0 - Migrazione da SQLite a PostgreSQL per deploy cloud
"""

import psycopg2
import psycopg2.errors
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
from datetime import datetime


class ExpenseDB:
    """Gestisce il database PostgreSQL delle spese"""

    def __init__(self):
        self.database_url = st.secrets["database"]["url"]
        # SQLAlchemy engine per pandas to_sql()
        self.engine = create_engine(self.database_url)
        self.init_database()

    def _get_conn(self):
        """Restituisce una nuova connessione psycopg2"""
        return psycopg2.connect(self.database_url)

    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Tabella transazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella categorie
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                budget REAL DEFAULT 0,
                color TEXT,
                icon TEXT
            )
        ''')

        # Tabella alert budget
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                threshold_percentage INTEGER DEFAULT 90,
                alert_sent BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (category) REFERENCES categories(name)
            )
        ''')

        # Tabella impostazioni utente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Tabella apprendimento merchant -> categoria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS merchant_categories (
                id SERIAL PRIMARY KEY,
                merchant TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
        ''')

        # Tabella spese ricorrenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                frequency TEXT NOT NULL CHECK(frequency IN ('mensile', 'settimanale', 'annuale')),
                day_of_period INTEGER,
                start_date DATE NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                last_generated DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category) REFERENCES categories(name)
            )
        ''')

        # Tabella apprendimento pattern entrate -> categoria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_income_patterns (
                id SERIAL PRIMARY KEY,
                description_pattern TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                learned_count INTEGER DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

        # Aggiungi categorie predefinite se non esistono
        self._add_default_categories(cursor, conn)

        conn.close()

    def _add_default_categories(self, cursor, conn):
        """Aggiunge categorie predefinite al primo avvio"""
        default_categories = [
            ('Alimentari', 500, '#FF6B6B', 'fa-cart-shopping'),
            ('Trasporti', 200, '#4ECDC4', 'fa-car'),
            ('Utenze', 300, '#45B7D1', 'fa-bolt'),
            ('Ristoranti', 250, '#FFA07A', 'fa-utensils'),
            ('Shopping', 200, '#98D8C8', 'fa-bag-shopping'),
            ('Salute', 150, '#F7DC6F', 'fa-heart-pulse'),
            ('Svago', 150, '#BB8FCE', 'fa-film'),
            ('Casa', 400, '#85C1E2', 'fa-house'),
            ('Entrate', 0, '#2ECC71', 'fa-money-bill-wave'),
            ('Altro', 100, '#95A5A6', 'fa-box'),
            ('Non Categorizzato', 0, '#BDC3C7', 'fa-circle-question')
        ]

        for name, budget, color, icon in default_categories:
            try:
                cursor.execute(
                    'INSERT INTO categories (name, budget, color, icon) VALUES (%s, %s, %s, %s) ON CONFLICT (name) DO NOTHING',
                    (name, budget, color, icon)
                )
            except Exception:
                pass

        conn.commit()

    def insert_transactions(self, df):
        """Inserisce transazioni dal DataFrame evitando duplicati"""
        conn = self._get_conn()

        # Assicurati che le colonne necessarie esistano
        required_columns = ['date', 'description', 'amount', 'category']
        for col in required_columns:
            if col not in df.columns:
                if col == 'category':
                    df[col] = 'Non Categorizzato'
                elif col == 'notes':
                    df[col] = ''

        # Inserisci solo le colonne rilevanti
        df_to_insert = df[['date', 'description', 'amount', 'category']].copy()
        if 'notes' in df.columns:
            df_to_insert['notes'] = df['notes']
        else:
            df_to_insert['notes'] = ''

        # Chiave univoca: data + descrizione + importo
        df_to_insert['_key'] = (
            df_to_insert['date'].astype(str) + '|' +
            df_to_insert['description'].astype(str) + '|' +
            df_to_insert['amount'].astype(str)
        )
        # Indice di occorrenza per ogni chiave nel CSV (0 = prima volta, 1 = seconda, ...)
        # Gestisce il caso legittimo: stesso importo, stesso merchant, stesso giorno (es. 2 caffè)
        df_to_insert['_count_csv'] = df_to_insert.groupby('_key').cumcount()

        # Quante volte ogni chiave esiste già nel DB
        existing = pd.read_sql_query(
            "SELECT date, description, amount FROM transactions",
            conn
        )
        conn.close()

        if len(existing) > 0:
            existing['_key'] = (
                existing['date'].astype(str) + '|' +
                existing['description'].astype(str) + '|' +
                existing['amount'].astype(str)
            )
            existing_counts = existing['_key'].value_counts()
            df_to_insert['_db_count'] = df_to_insert['_key'].map(existing_counts).fillna(0).astype(int)
            # Mantieni solo le occorrenze in eccesso rispetto a quelle già nel DB
            df_to_insert = df_to_insert[df_to_insert['_count_csv'] >= df_to_insert['_db_count']].copy()

        df_to_insert = df_to_insert.drop(columns=[c for c in ['_key', '_count_csv', '_db_count'] if c in df_to_insert.columns])

        # Inserisci solo se ci sono transazioni non duplicate
        if len(df_to_insert) > 0:
            df_to_insert.to_sql('transactions', self.engine, if_exists='append', index=False)

        return len(df_to_insert)  # Ritorna numero di transazioni inserite

    def get_all_transactions(self):
        """Recupera tutte le transazioni"""
        conn = self._get_conn()
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
        conn.close()
        return df

    def get_transactions_by_date_range(self, start_date, end_date):
        """Recupera transazioni in un intervallo di date"""
        conn = self._get_conn()
        query = """
            SELECT * FROM transactions
            WHERE date BETWEEN %s AND %s
            ORDER BY date DESC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df

    def get_transactions_by_category(self, category):
        """Recupera transazioni per categoria"""
        conn = self._get_conn()
        query = "SELECT * FROM transactions WHERE category = %s ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=(category,))
        conn.close()
        return df

    def update_transaction_category(self, transaction_id, new_category):
        """Aggiorna la categoria di una transazione"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transactions SET category = %s WHERE id = %s",
            (new_category, transaction_id)
        )
        conn.commit()
        conn.close()

    def delete_transaction(self, transaction_id):
        """Elimina una transazione"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
        conn.commit()
        conn.close()

    def get_categories(self):
        """Recupera tutte le categorie"""
        conn = self._get_conn()
        df = pd.read_sql_query("SELECT * FROM categories ORDER BY name", conn)
        conn.close()
        return df

    def add_category(self, name, budget=0, color='#95A5A6', icon='📦'):
        """Aggiunge una nuova categoria"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO categories (name, budget, color, icon) VALUES (%s, %s, %s, %s)',
                (name, budget, color, icon)
            )
            conn.commit()
            success = True
        except psycopg2.errors.UniqueViolation:
            success = False
        finally:
            conn.close()
        return success

    def update_category_budget(self, category_name, new_budget):
        """Aggiorna il budget di una categoria"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET budget = %s WHERE name = %s",
            (new_budget, category_name)
        )
        conn.commit()
        conn.close()

    def update_category(self, old_name, new_name, new_budget, new_color, new_icon):
        """
        Aggiorna tutti i dati di una categoria

        Args:
            old_name: Nome corrente della categoria
            new_name: Nuovo nome
            new_budget: Nuovo budget
            new_color: Nuovo colore
            new_icon: Nuova icona

        Returns:
            True se successo, False se il nuovo nome esiste già
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Se il nome è cambiato, aggiorna anche le transazioni
            if old_name != new_name:
                # Verifica che il nuovo nome non esista già
                cursor.execute("SELECT COUNT(*) FROM categories WHERE name = %s", (new_name,))
                if cursor.fetchone()[0] > 0:
                    conn.close()
                    return False

                # Aggiorna le transazioni con il nuovo nome categoria
                cursor.execute(
                    "UPDATE transactions SET category = %s WHERE category = %s",
                    (new_name, old_name)
                )

            # Aggiorna la categoria
            cursor.execute(
                "UPDATE categories SET name = %s, budget = %s, color = %s, icon = %s WHERE name = %s",
                (new_name, new_budget, new_color, new_icon, old_name)
            )

            conn.commit()
            success = True
        except psycopg2.errors.UniqueViolation:
            success = False
        finally:
            conn.close()

        return success

    def delete_category(self, category_name):
        """Elimina una categoria (le transazioni associate diventano 'Non Categorizzato')"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Aggiorna le transazioni con questa categoria
        cursor.execute(
            "UPDATE transactions SET category = 'Non Categorizzato' WHERE category = %s",
            (category_name,)
        )

        # Elimina la categoria
        cursor.execute("DELETE FROM categories WHERE name = %s", (category_name,))

        conn.commit()
        conn.close()

    def get_monthly_summary(self, year, month):
        """Ottieni riepilogo mensile"""
        conn = self._get_conn()
        query = """
            SELECT
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions
            WHERE EXTRACT(YEAR FROM date::date) = %s AND EXTRACT(MONTH FROM date::date) = %s
            GROUP BY category
            ORDER BY total DESC
        """
        df = pd.read_sql_query(query, conn, params=(year, month))
        conn.close()
        return df

    def get_category_totals(self):
        """Ottieni totali per categoria (tutti i tempi)"""
        conn = self._get_conn()
        query = """
            SELECT
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions
            GROUP BY category
            ORDER BY total DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def learn_merchant_category(self, merchant, category):
        """Impara o aggiorna associazione merchant -> categoria"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Verifica se esiste già
        cursor.execute("SELECT usage_count FROM merchant_categories WHERE merchant = %s", (merchant,))
        result = cursor.fetchone()

        if result:
            # Aggiorna categoria e incrementa contatore
            cursor.execute(
                "UPDATE merchant_categories SET category = %s, usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP WHERE merchant = %s",
                (category, merchant)
            )
        else:
            # Inserisci nuovo
            cursor.execute(
                "INSERT INTO merchant_categories (merchant, category) VALUES (%s, %s)",
                (merchant, category)
            )

        conn.commit()
        conn.close()

    def get_learned_category(self, merchant):
        """Ottieni categoria appresa per un merchant"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM merchant_categories WHERE merchant = %s", (merchant,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_learned_merchants(self):
        """Ottieni tutte le associazioni merchant -> categoria"""
        conn = self._get_conn()
        df = pd.read_sql_query(
            "SELECT merchant, category, usage_count, last_used FROM merchant_categories ORDER BY usage_count DESC",
            conn
        )
        conn.close()
        return df

    def delete_learned_merchant(self, merchant):
        """Elimina un'associazione merchant -> categoria appresa"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM merchant_categories WHERE merchant = %s", (merchant,))
        conn.commit()
        conn.close()

    # ========== GESTIONE SPESE RICORRENTI ==========

    def add_recurring_expense(self, name, category, amount, frequency, day_of_period, start_date, notes=''):
        """Aggiunge una nuova spesa ricorrente"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recurring_expenses (name, category, amount, frequency, day_of_period, start_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (name, category, amount, frequency, day_of_period, start_date, notes))
        conn.commit()
        conn.close()

    def get_recurring_expenses(self, active_only=True):
        """Recupera tutte le spese ricorrenti"""
        conn = self._get_conn()
        query = "SELECT * FROM recurring_expenses"
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY name"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_recurring_expense_by_id(self, rec_id):
        """Recupera una spesa ricorrente specifica"""
        conn = self._get_conn()
        df = pd.read_sql_query("SELECT * FROM recurring_expenses WHERE id = %s", conn, params=(rec_id,))
        conn.close()
        return df.iloc[0] if len(df) > 0 else None

    def update_recurring_expense(self, rec_id, name, category, amount, frequency, day_of_period, start_date, notes=''):
        """Aggiorna una spesa ricorrente"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE recurring_expenses
            SET name = %s, category = %s, amount = %s, frequency = %s, day_of_period = %s, start_date = %s, notes = %s
            WHERE id = %s
        ''', (name, category, amount, frequency, day_of_period, start_date, notes, rec_id))
        conn.commit()
        conn.close()

    def toggle_recurring_expense(self, rec_id, active):
        """Attiva/disattiva una spesa ricorrente"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE recurring_expenses SET active = %s WHERE id = %s", (active, rec_id))
        conn.commit()
        conn.close()

    def delete_recurring_expense(self, rec_id):
        """Elimina una spesa ricorrente"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recurring_expenses WHERE id = %s", (rec_id,))
        conn.commit()
        conn.close()

    def get_recurring_expenses_for_month(self, year, month):
        """Recupera le spese ricorrenti previste per un dato mese"""
        conn = self._get_conn()
        df = pd.read_sql_query('''
            SELECT * FROM recurring_expenses
            WHERE active = TRUE AND (frequency = 'mensile' OR frequency = 'annuale')
        ''', conn)
        conn.close()

        # Filtra solo le ricorrenti applicabili al mese richiesto
        if len(df) > 0:
            df['start_date'] = pd.to_datetime(df['start_date'])
            current_date = pd.to_datetime(f"{year}-{month:02d}-01")
            df = df[df['start_date'] <= current_date]

        return df

    # ========== GESTIONE APPRENDIMENTO ENTRATE ==========

    def normalize_income_description(self, description):
        """
        Normalizza descrizione entrata per pattern matching

        Rimuove:
        - Date variabili (mesi, anni, numeri di giorni)
        - Numeri di riferimento lunghi
        - Spazi multipli

        Mantiene:
        - Keywords principali (ente, tipo operazione)
        - Parole significative

        Args:
            description: Descrizione originale

        Returns:
            Descrizione normalizzata
        """
        import re

        if not description:
            return ""

        # Converti in lowercase
        desc = str(description).lower().strip()

        # Rimuovi date comuni: gen, feb, mar, 2024, 2025, ecc.
        months = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic',
                  'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                  'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
        for month in months:
            desc = re.sub(r'\b' + month + r'\b', '', desc)

        # Rimuovi anni (2020-2099)
        desc = re.sub(r'\b20[2-9][0-9]\b', '', desc)

        # Rimuovi numeri di giorni standalone (01-31)
        desc = re.sub(r'\b[0-3]?[0-9]\b(?![a-z])', '', desc)

        # Rimuovi numeri di riferimento lunghi (più di 3 cifre consecutive)
        desc = re.sub(r'\d{4,}', '', desc)

        # Rimuovi punteggiatura eccessiva
        desc = re.sub(r'[.,;:]+', ' ', desc)

        # Normalizza spazi multipli
        desc = re.sub(r'\s+', ' ', desc).strip()

        return desc

    def save_income_pattern(self, description, category):
        """
        Salva o aggiorna pattern appreso per entrate

        Args:
            description: Descrizione originale della transazione
            category: Categoria assegnata dall'utente
        """
        # Normalizza descrizione
        pattern = self.normalize_income_description(description)

        if not pattern:
            return  # Evita pattern vuoti

        conn = self._get_conn()
        cursor = conn.cursor()

        # Verifica se esiste già
        cursor.execute("SELECT learned_count FROM learned_income_patterns WHERE description_pattern = %s", (pattern,))
        result = cursor.fetchone()

        if result:
            # Aggiorna categoria e incrementa contatore
            cursor.execute(
                "UPDATE learned_income_patterns SET category = %s, learned_count = learned_count + 1, last_updated = CURRENT_TIMESTAMP WHERE description_pattern = %s",
                (category, pattern)
            )
        else:
            # Inserisci nuovo pattern
            cursor.execute(
                "INSERT INTO learned_income_patterns (description_pattern, category) VALUES (%s, %s)",
                (pattern, category)
            )

        conn.commit()
        conn.close()

    def get_learned_income_category(self, description):
        """
        Ottieni categoria appresa per una descrizione entrata

        Usa matching parziale: cerca se il pattern appreso è contenuto nella descrizione

        Args:
            description: Descrizione della transazione

        Returns:
            Categoria appresa o None se non trovata
        """
        pattern = self.normalize_income_description(description)

        if not pattern:
            return None

        conn = self._get_conn()
        cursor = conn.cursor()

        # Cerca match esatto prima
        cursor.execute("SELECT category FROM learned_income_patterns WHERE description_pattern = %s", (pattern,))
        result = cursor.fetchone()

        if result:
            conn.close()
            return result[0]

        # Se non trova match esatto, cerca pattern contenuti nella descrizione
        # Ordina per lunghezza pattern (più lunghi = più specifici = priorità)
        cursor.execute("""
            SELECT category, description_pattern
            FROM learned_income_patterns
            ORDER BY LENGTH(description_pattern) DESC, learned_count DESC
        """)

        results = cursor.fetchall()
        conn.close()

        # Cerca il pattern più lungo che è contenuto nella descrizione
        for category, learned_pattern in results:
            # Controlla se tutte le parole del pattern sono nella descrizione
            pattern_words = learned_pattern.split()
            if all(word in pattern for word in pattern_words):
                return category

        return None

    def get_all_learned_income_patterns(self):
        """Ottieni tutti i pattern entrate appresi"""
        conn = self._get_conn()
        df = pd.read_sql_query(
            "SELECT description_pattern, category, learned_count, last_updated FROM learned_income_patterns ORDER BY learned_count DESC",
            conn
        )
        conn.close()
        return df

    def delete_learned_income_pattern(self, pattern):
        """Elimina un pattern entrata appreso"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM learned_income_patterns WHERE description_pattern = %s", (pattern,))
        conn.commit()
        conn.close()
