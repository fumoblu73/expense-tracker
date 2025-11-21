"""
Database Manager per l'app di gestione spese familiari
Gestisce tutte le operazioni CRUD con SQLite
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime


class ExpenseDB:
    """Gestisce il database SQLite delle spese"""

    def __init__(self, db_path="data/expenses.db"):
        self.db_path = db_path
        Path("data").mkdir(exist_ok=True)
        self.init_database()

    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabella transazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                budget REAL DEFAULT 0,
                color TEXT,
                icon TEXT
            )
        ''')

        # Tabella alert budget
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                threshold_percentage INTEGER DEFAULT 90,
                alert_sent BOOLEAN DEFAULT 0,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
        ''')

        conn.commit()

        # Aggiungi categorie predefinite se non esistono
        self._add_default_categories(cursor, conn)

        conn.close()

    def _add_default_categories(self, cursor, conn):
        """Aggiunge categorie predefinite al primo avvio"""
        default_categories = [
            ('Alimentari', 500, '#FF6B6B', '🛒'),
            ('Trasporti', 200, '#4ECDC4', '🚗'),
            ('Utenze', 300, '#45B7D1', '💡'),
            ('Ristoranti', 250, '#FFA07A', '🍽️'),
            ('Shopping', 200, '#98D8C8', '🛍️'),
            ('Salute', 150, '#F7DC6F', '⚕️'),
            ('Svago', 150, '#BB8FCE', '🎬'),
            ('Casa', 400, '#85C1E2', '🏠'),
            ('Entrate', 0, '#2ECC71', '💰'),
            ('Altro', 100, '#95A5A6', '📦'),
            ('Non Categorizzato', 0, '#BDC3C7', '❓')
        ]

        for name, budget, color, icon in default_categories:
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO categories (name, budget, color, icon) VALUES (?, ?, ?, ?)',
                    (name, budget, color, icon)
                )
            except:
                pass

        conn.commit()

    def insert_transactions(self, df):
        """Inserisce transazioni dal DataFrame"""
        conn = sqlite3.connect(self.db_path)

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

        df_to_insert.to_sql('transactions', conn, if_exists='append', index=False)
        conn.close()

    def get_all_transactions(self):
        """Recupera tutte le transazioni"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
        conn.close()
        return df

    def get_transactions_by_date_range(self, start_date, end_date):
        """Recupera transazioni in un intervallo di date"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM transactions
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df

    def get_transactions_by_category(self, category):
        """Recupera transazioni per categoria"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM transactions WHERE category = ? ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=(category,))
        conn.close()
        return df

    def update_transaction_category(self, transaction_id, new_category):
        """Aggiorna la categoria di una transazione"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transactions SET category = ? WHERE id = ?",
            (new_category, transaction_id)
        )
        conn.commit()
        conn.close()

    def delete_transaction(self, transaction_id):
        """Elimina una transazione"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()

    def get_categories(self):
        """Recupera tutte le categorie"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM categories ORDER BY name", conn)
        conn.close()
        return df

    def add_category(self, name, budget=0, color='#95A5A6', icon='📦'):
        """Aggiunge una nuova categoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO categories (name, budget, color, icon) VALUES (?, ?, ?, ?)',
                (name, budget, color, icon)
            )
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        finally:
            conn.close()
        return success

    def update_category_budget(self, category_name, new_budget):
        """Aggiorna il budget di una categoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET budget = ? WHERE name = ?",
            (new_budget, category_name)
        )
        conn.commit()
        conn.close()

    def delete_category(self, category_name):
        """Elimina una categoria (le transazioni associate diventano 'Non Categorizzato')"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Aggiorna le transazioni con questa categoria
        cursor.execute(
            "UPDATE transactions SET category = 'Non Categorizzato' WHERE category = ?",
            (category_name,)
        )

        # Elimina la categoria
        cursor.execute("DELETE FROM categories WHERE name = ?", (category_name,))

        conn.commit()
        conn.close()

    def get_monthly_summary(self, year, month):
        """Ottieni riepilogo mensile"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category
            ORDER BY total DESC
        """
        df = pd.read_sql_query(query, conn, params=(str(year), f"{month:02d}"))
        conn.close()
        return df

    def get_category_totals(self):
        """Ottieni totali per categoria (tutti i tempi)"""
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verifica se esiste già
        cursor.execute("SELECT usage_count FROM merchant_categories WHERE merchant = ?", (merchant,))
        result = cursor.fetchone()

        if result:
            # Aggiorna categoria e incrementa contatore
            cursor.execute(
                "UPDATE merchant_categories SET category = ?, usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP WHERE merchant = ?",
                (category, merchant)
            )
        else:
            # Inserisci nuovo
            cursor.execute(
                "INSERT INTO merchant_categories (merchant, category) VALUES (?, ?)",
                (merchant, category)
            )

        conn.commit()
        conn.close()

    def get_learned_category(self, merchant):
        """Ottieni categoria appresa per un merchant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM merchant_categories WHERE merchant = ?", (merchant,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_learned_merchants(self):
        """Ottieni tutte le associazioni merchant -> categoria"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT merchant, category, usage_count, last_used FROM merchant_categories ORDER BY usage_count DESC",
            conn
        )
        conn.close()
        return df

    def delete_learned_merchant(self, merchant):
        """Elimina un'associazione merchant -> categoria appresa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM merchant_categories WHERE merchant = ?", (merchant,))
        conn.commit()
        conn.close()
