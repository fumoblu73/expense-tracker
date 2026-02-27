"""
Family Expense Tracker
App web per gestione e monitoraggio spese familiari

Creata per essere semplice, mobile-friendly e completamente gratuita
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Aggiungi directory corrente al path
sys.path.append(str(Path(__file__).parent))

# Import moduli personalizzati
from database.db_manager import ExpenseDB
from utils.csv_parser import parse_bank_csv, validate_csv_preview, get_sample_csv_template
from utils.smart_categorization import smart_categorize_transactions, extract_merchant
from utils.backup_manager import create_full_backup, extract_backup_info, restore_backup, get_backup_filename
from utils.recurring_utils import calculate_available_balance, get_recurring_status_for_month
from utils.anomaly_detection import get_anomaly_summary
from utils.formatters import format_currency_ita
from utils.visualizations import (
    create_monthly_summary,
    create_category_pie,
    create_budget_comparison,
    create_monthly_category_vs_budget,
    create_income_vs_expenses_trend,
    create_top_expenses_table,
    create_category_trend,
    style_transaction_amounts
)
from utils.budget_alerts import (
    check_budget_alerts,
    display_alerts,
    create_budget_summary_card,
    display_budget_summary,
    get_budget_recommendations,
    display_recommendations
)
from utils.forecasting import (
    simple_moving_average_forecast,
    plot_forecast,
    category_trend_analysis,
    calculate_spending_statistics,
    display_statistics,
    compare_periods,
    display_period_comparison
)
from utils.email_sender import send_monthly_report, configure_email_settings
from utils.icon_selector import ICON_LIBRARY, get_fontawesome_cdn, render_icon_html, search_icons

# Configurazione pagina
st.set_page_config(
    page_title="Family Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carica Font Awesome CDN
st.markdown(get_fontawesome_cdn(), unsafe_allow_html=True)

# CSS personalizzato per mobile
st.markdown("""
<style>
    /* Migliora l'esperienza mobile */
    .stButton button {
        width: 100%;
        height: 50px;
        font-size: 16px;
        font-weight: bold;
    }

    .stFileUploader label {
        font-size: 18px;
        font-weight: bold;
    }

    /* Card stile migliore */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Spacing migliore su mobile */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem;
        }
    }

    /* Header personalizzato */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Inizializza database
@st.cache_resource
def get_database():
    """Crea e restituisce istanza database"""
    return ExpenseDB()

def migrate_emoji_to_fontawesome(db):
    """
    Migra automaticamente le emoji a Font Awesome al primo caricamento
    """
    # Mapping emoji → Font Awesome
    emoji_to_fa_map = {
        '🛒': 'fa-cart-shopping',
        '🚗': 'fa-car',
        '💡': 'fa-bolt',
        '🍽️': 'fa-utensils',
        '🛍️': 'fa-bag-shopping',
        '⚕️': 'fa-heart-pulse',
        '🎬': 'fa-film',
        '🏠': 'fa-house',
        '💰': 'fa-money-bill-wave',
        '📦': 'fa-box',
        '❓': 'fa-circle-question',
        '💳': 'fa-credit-card',
        '📱': 'fa-mobile-screen',
        '✈️': 'fa-plane',
        '⚡': 'fa-bolt',
        '🍕': 'fa-pizza-slice',
        '🎁': 'fa-gift',
        '💊': 'fa-pills',
        '🏃': 'fa-person-running',
        '📚': 'fa-book',
        '🐾': 'fa-paw',
    }

    conn = db._get_conn()
    cursor = conn.cursor()

    # Aggiorna solo le emoji che sono nella mappa
    for emoji, fa_icon in emoji_to_fa_map.items():
        cursor.execute(
            "UPDATE categories SET icon = %s WHERE icon = %s",
            (fa_icon, emoji)
        )

    conn.commit()
    conn.close()

db = get_database()

# Esegui migrazione icone automaticamente (solo la prima volta per sessione)
if 'icons_migrated' not in st.session_state:
    migrate_emoji_to_fontawesome(db)
    st.session_state['icons_migrated'] = True


def get_quarterly_withdrawals(transactions_df):
    """Conta prelievi per persona nel trimestre corrente"""
    now = datetime.now()
    q = (now.month - 1) // 3          # 0=Q1, 1=Q2, 2=Q3, 3=Q4
    q_start = q * 3 + 1               # mese iniziale trimestre (1,4,7,10)
    q_end = q_start + 2               # mese finale trimestre (3,6,9,12)

    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    q_df = df[
        (df['date'].dt.year == now.year) &
        (df['date'].dt.month >= q_start) &
        (df['date'].dt.month <= q_end)
    ]

    return {
        'Emanuele': int(len(q_df[q_df['category'] == 'Prelievo Emanuele'])),
        'Cinzia':   int(len(q_df[q_df['category'] == 'Prelievo Cinzia'])),
        'label':    f"T{q + 1} {now.year}"
    }


def main():
    """Funzione principale dell'app"""

    # Header principale
    st.markdown("""
    <div class="main-header">
        <h1>💰 Family Expense Tracker</h1>
        <p>Gestisci le tue spese familiari in modo semplice e intelligente</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar per navigazione
    with st.sidebar:
        st.image("https://em-content.zobj.net/thumbs/240/apple/354/money-bag_1f4b0.png", width=80)
        st.title("Menu")

        page = st.radio(
            "Navigazione",
            [
                "🏠 Dashboard",
                "📤 Carica Dati",
                "🏷️ Gestisci Categorie",
                "💳 Spese Ricorrenti",
                "📊 Report & Analisi",
                "🔮 Previsioni",
                "⚙️ Impostazioni",
                "❓ Guida"
            ],
            label_visibility="collapsed"
        )

        st.divider()

        # Quick stats nella sidebar
        transactions = db.get_all_transactions()
        if len(transactions) > 0:
            st.metric("Totale Transazioni", len(transactions))
            st.metric("Spesa Totale", format_currency_ita(transactions['amount'].sum()))

            # Ultima transazione
            transactions['date'] = pd.to_datetime(transactions['date'])
            last_date = transactions['date'].max()
            st.caption(f"Ultimo aggiornamento: {last_date.strftime('%d/%m/%Y')}")

    # Routing pagine
    if "Dashboard" in page:
        show_dashboard()
    elif "Carica Dati" in page:
        show_upload_page()
    elif "Categorie" in page:
        show_categories_page()
    elif "Ricorrenti" in page:
        show_recurring_expenses_page()
    elif "Report" in page:
        show_reports_page()
    elif "Previsioni" in page:
        show_forecasting_page()
    elif "Impostazioni" in page:
        show_settings_page()
    elif "Guida" in page:
        show_help_page()


def show_dashboard():
    """Pagina dashboard principale"""
    st.title("🏠 Dashboard")

    transactions = db.get_all_transactions()

    if len(transactions) == 0:
        st.info("""
        👋 Benvenuto! Inizia caricando i tuoi dati bancari.

        Vai su **📤 Carica Dati** nella sidebar per importare il tuo primo file CSV.
        """)
        return

    # Converti date
    transactions['date'] = pd.to_datetime(transactions['date'])
    categories = db.get_categories()

    # Statistiche rapide
    current_month = pd.Period.now('M')
    month_transactions = transactions[transactions['date'].dt.to_period('M') == current_month]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_month = month_transactions['amount'].sum()
        st.metric("Spesa Mese Corrente", format_currency_ita(total_month))

    with col2:
        count_month = len(month_transactions)
        st.metric("Transazioni Mese", count_month)

    with col3:
        avg_transaction = month_transactions['amount'].mean() if len(month_transactions) > 0 else 0
        st.metric("Media Transazione", format_currency_ita(avg_transaction))

    with col4:
        days_in_month = datetime.now().day
        daily_avg = total_month / days_in_month if days_in_month > 0 else 0
        st.metric("Media Giornaliera", format_currency_ita(daily_avg))

    st.divider()

    # Card Budget Disponibile & Spese Ricorrenti
    recurring = db.get_recurring_expenses(active_only=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Budget Disponibile
        balance_info = calculate_available_balance(
            transactions, categories, recurring,
            datetime.now().year, datetime.now().month
        )

        st.markdown("### 💰 Budget Disponibile")

        # Colore basato su stato
        if balance_info['is_negative']:
            color = "🔴"
            status_text = "SUPERATO"
        elif balance_info['available'] < balance_info['total_budget'] * 0.1:
            color = "🟠"
            status_text = "ATTENZIONE"
        else:
            color = "🟢"
            status_text = "OK"

        st.metric(
            f"{color} Disponibile per {balance_info['days_remaining']} giorni",
            format_currency_ita(balance_info['available']),
            f"{status_text}"
        )

        # Dettaglio
        with st.expander("📊 Dettaglio Calcolo"):
            st.write(f"**Budget Totale**: {format_currency_ita(balance_info['total_budget'])}")
            st.write(f"**Speso fino ad oggi**: -{format_currency_ita(balance_info['spent'])}")
            st.write(f"**Spese ricorrenti da pagare**: -{format_currency_ita(balance_info['recurring_pending'])}")
            st.write("─" * 40)
            st.write(f"**Disponibile**: {format_currency_ita(balance_info['available'])}")

            if balance_info['days_remaining'] > 0:
                st.info(f"💡 Puoi spendere **{format_currency_ita(balance_info['daily_allowance'])}** al giorno per i prossimi **{balance_info['days_remaining']} giorni**")

    with col2:
        # Spese Ricorrenti
        st.markdown("### 💳 Spese Ricorrenti")

        if len(recurring) == 0:
            st.info("Nessuna spesa ricorrente configurata")
            if st.button("➕ Aggiungi Prima Ricorrente", use_container_width=True):
                st.session_state['page'] = "💳 Spese Ricorrenti"
                st.rerun()
        else:
            # Calcola totale mensile
            total_recurring = 0
            for _, rec in recurring.iterrows():
                if rec['frequency'] == 'mensile':
                    total_recurring += rec['amount']
                elif rec['frequency'] == 'annuale':
                    total_recurring += rec['amount'] / 12

            st.metric("Totale Mensile", format_currency_ita(total_recurring))

            # Status ricorrenti
            recurring_status = get_recurring_status_for_month(transactions, recurring)

            if len(recurring_status) > 0:
                paid_count = len(recurring_status[recurring_status['status'] == 'paid'])
                pending_count = len(recurring_status[recurring_status['status'] == 'pending'])

                st.write(f"✅ Pagate: {paid_count}")
                st.write(f"⏳ Da pagare: {pending_count}")

            if st.button("📋 Gestisci", use_container_width=True):
                st.session_state['page'] = "💳 Spese Ricorrenti"
                st.rerun()

    st.divider()

    # ── Prelievi Bancomat Trimestrali ─────────────────────────────────────
    w = get_quarterly_withdrawals(transactions)
    has_any = w['Emanuele'] > 0 or w['Cinzia'] > 0
    with st.expander(f"🏧 Prelievi Bancomat — {w['label']}", expanded=has_any):
        col1, col2 = st.columns(2)
        for col, name in [(col1, 'Emanuele'), (col2, 'Cinzia')]:
            with col:
                n = w[name]
                remaining = max(0, 3 - n)
                if n == 0:
                    icon, status = "🟢", "Nessun prelievo effettuato"
                elif n < 3:
                    icon, status = "🟡", f"{remaining} prelievo/i gratuito/i rimanente/i"
                elif n == 3:
                    icon, status = "🔴", "Limite di 3 prelievi gratuiti raggiunto"
                else:
                    icon, status = "⛔", f"⚠️ Superato il limite! ({n - 3} a pagamento)"
                st.metric(f"{icon} {name}", f"prelievo n. {n} di 3", delta=status,
                          delta_color="off")

    # Alert Budget (nascondibili)
    alerts = check_budget_alerts(transactions, categories, current_month)
    if alerts:
        summary = create_budget_summary_card(alerts)

        with st.expander("⚠️ Alert Budget", expanded=False):
            display_budget_summary(summary)
            st.divider()
            display_alerts(alerts, show_all=False)

    # Anomalie di Spesa (nascondibili)
    anomaly_summary = get_anomaly_summary(transactions, lookback_months=3)

    if anomaly_summary['total_count'] > 0:
        with st.expander(f"🔍 Anomalie Rilevate ({anomaly_summary['total_count']})", expanded=False):
            # Anomalie per importo
            if len(anomaly_summary['amount_anomalies']) > 0:
                st.subheader("💸 Transazioni con Importi Anomali")

                for idx, row in anomaly_summary['amount_anomalies'].head(5).iterrows():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        severity_icon = "🔴" if row['severity'] == 'high' else "🟠"
                        st.write(f"{severity_icon} **{row['description']}**")
                        st.caption(f"Data: {row['date'].strftime('%d/%m/%Y')}")

                    with col2:
                        st.metric("Importo", format_currency_ita(row['amount']))
                        st.caption(f"Media: {format_currency_ita(row['mean_amount'])}")

                    with col3:
                        st.write(f"**+{row['deviation_pct']:.0f}%**")
                        st.caption(row['explanation'])

                if len(anomaly_summary['amount_anomalies']) > 5:
                    st.caption(f"... e altre {len(anomaly_summary['amount_anomalies']) - 5} anomalie")

            # Anomalie per frequenza
            if len(anomaly_summary['frequency_anomalies']) > 0:
                st.divider()
                st.subheader("🔄 Merchant con Frequenza Insolita")

                for idx, row in anomaly_summary['frequency_anomalies'].head(3).iterrows():
                    st.write(f"**{row['merchant']}**: {row['transaction_count']} transazioni ({format_currency_ita(row['total_amount'])} totale)")
                    st.caption(row['explanation'])

    st.divider()

    # Grafici principali - OGNI GRAFICO NASCONDIBILE SINGOLARMENTE
    st.subheader("📊 Grafici Analisi")

    # Row 1: Andamento mensile e Categorie
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("📈 Andamento Spese Mensili", expanded=True):
            fig_monthly = create_monthly_summary(transactions)
            if fig_monthly:
                st.plotly_chart(fig_monthly, use_container_width=True)

    with col2:
        with st.expander("🏷️ Spese per Categoria", expanded=True):
            fig_pie = create_category_pie(transactions, categories)
            if fig_pie:
                st.plotly_chart(fig_pie, use_container_width=True)

    # Budget vs Spesa Effettiva
    with st.expander("💰 Budget vs Spesa Effettiva", expanded=True):
        fig_budget = create_budget_comparison(transactions, categories, current_month)
        if fig_budget:
            st.plotly_chart(fig_budget, use_container_width=True)

    # Andamento mensile categorie vs budget
    with st.expander("📊 Andamento Mensile Categorie vs Budget", expanded=False):
        # Prepara lista categorie con budget
        categories_with_budget = categories[categories['budget'] > 0]['name'].tolist()
        income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso', 'Sussidi', 'Investimenti', 'Altro Reddito']
        categories_with_budget = [c for c in categories_with_budget if c not in income_categories]

        if len(categories_with_budget) > 0:
            selected_category = st.selectbox(
                "Seleziona Categoria",
                options=["Tutte"] + categories_with_budget,
                key="category_trend_selector"
            )

            fig_cat_budget = create_monthly_category_vs_budget(transactions, categories, selected_category)
            if fig_cat_budget:
                st.plotly_chart(fig_cat_budget, use_container_width=True)
        else:
            st.info("💡 Imposta i budget nelle categorie per visualizzare questo grafico")

    # Confronto entrate vs spese mensili
    with st.expander("💰 Entrate vs Spese Mensili", expanded=False):
        fig_income_expenses = create_income_vs_expenses_trend(transactions, months=6)
        if fig_income_expenses:
            st.plotly_chart(fig_income_expenses, use_container_width=True)

    # Top spese
    st.subheader("💸 Top 10 Spese del Mese")

    # Categorie che sono ENTRATE
    income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso', 'Sussidi', 'Investimenti', 'Altro Reddito']

    # Conta entrate vs spese
    income_count = len(month_transactions[month_transactions['category'].isin(income_categories)])
    expense_count = len(month_transactions[~month_transactions['category'].isin(income_categories)])

    if income_count > 0 and expense_count == 0:
        st.info(f"""
        📊 **Nota**: Questo mese sono state registrate solo **{income_count} entrate** (bonifici, rimborsi, stipendi, pensioni).

        Per vedere le categorie di spesa (Alimentari, Utenze, Trasporti, ecc.), importa un file che contenga anche le **uscite/spese**.

        Le transazioni con importo **negativo** nel file bancario vengono categorizzate automaticamente nelle varie categorie di spesa.
        """)

    top_expenses = create_top_expenses_table(month_transactions, limit=10)
    if top_expenses is not None:
        st.dataframe(top_expenses, use_container_width=True, hide_index=True)


def show_upload_page():
    """Pagina caricamento CSV"""
    st.title("📤 Carica Dati Bancari")

    st.info("""
    📋 **Come funziona:**
    1. Scarica il file CSV/Excel dalla tua banca
    2. Caricalo qui sotto
    3. Verifica l'anteprima
    4. Clicca su Salva

    Formati supportati: CSV, Excel (XLS/XLSX)
    """)

    st.success("""
    🧠 **Sistema di Apprendimento Intelligente Attivo!**

    L'app categorizza automaticamente le transazioni riconoscendo i merchant (negozi, ristoranti, ecc.) e impara dalle tue scelte!

    ✅ Categorizzazione automatica alla prima importazione
    ✅ Riconoscimento merchant da descrizioni bancarie
    ✅ Apprendimento continuo dalle tue correzioni
    """)

    # Template di esempio
    with st.expander("📥 Scarica Template di Esempio"):
        sample_df = get_sample_csv_template()
        st.dataframe(sample_df, use_container_width=True)

        csv = sample_df.to_csv(index=False)
        st.download_button(
            "⬇️ Scarica Template CSV",
            csv,
            "template_spese.csv",
            "text/csv",
            use_container_width=True
        )

    st.divider()

    # Upload file
    uploaded_file = st.file_uploader(
        "Trascina qui il tuo file CSV/Excel oppure clicca per selezionarlo",
        type=['csv', 'xlsx', 'xls'],
        help="Carica il file CSV o Excel (XLS/XLSX) scaricato dalla tua banca"
    )

    if uploaded_file:
        # Parse CSV
        df = parse_bank_csv(uploaded_file)

        if df is not None:
            # Mostra anteprima
            if validate_csv_preview(df, num_rows=10):

                # Categorizzazione automatica intelligente
                st.subheader("🧠 Categorizzazione Intelligente")

                col1, col2 = st.columns(2)
                with col1:
                    use_smart_cat = st.checkbox(
                        "✨ Usa categorizzazione automatica",
                        value=True,
                        help="Categorizza automaticamente usando intelligenza artificiale e apprendimento"
                    )
                with col2:
                    if use_smart_cat:
                        st.info("💡 L'app ricorderà le tue scelte per il futuro!")

                if use_smart_cat:
                    with st.spinner("🧠 Analisi transazioni in corso..."):
                        df = smart_categorize_transactions(df, db)

                    st.success("✅ Categorizzazione completata!")

                    # Mostra anteprima con merchant estratto
                    preview_cols = ['description', 'merchant', 'category', 'amount']
                    st.dataframe(df[preview_cols].head(15), use_container_width=True)

                # Salva nel database
                if st.button("💾 Salva nel Database", use_container_width=True, type="primary"):
                    with st.spinner("Salvataggio in corso..."):
                        try:
                            total_transactions = len(df)
                            saved_count = db.insert_transactions(df)
                            duplicates_count = total_transactions - saved_count

                            if duplicates_count > 0:
                                st.warning(f"⚠️ Trovati {duplicates_count} duplicati (già presenti nel database)")
                                st.success(f"✅ {saved_count} nuove transazioni salvate con successo!")
                            else:
                                st.success(f"✅ {saved_count} transazioni salvate con successo!")
                                st.balloons()

                            # Promemoria backup dopo import
                            if saved_count > 0:
                                st.divider()
                                st.info("""
                                💾 **Promemoria Importante: Backup dei Dati**

                                Hai appena importato nuove transazioni! Per proteggere i tuoi dati:
                                1. Vai su **⚙️ Impostazioni** → **Backup & Ripristino**
                                2. Scarica un backup completo (ZIP)
                                3. Salvalo su Dropbox, Google Drive o disco locale

                                ⚠️ I dati su Streamlit Cloud potrebbero essere persi durante un redeploy!
                                """)

                                col1, col2, col3 = st.columns([1, 1, 1])
                                with col2:
                                    if st.button("📥 Vai a Backup Ora", use_container_width=True, type="secondary"):
                                        st.session_state['page'] = "⚙️ Impostazioni"
                                        st.rerun()

                            # Suggerisci di categorizzare se ci sono nuove transazioni
                            if saved_count > 0 and not use_smart_cat:
                                st.info("💡 Vai su **🏷️ Gestisci Categorie** per categorizzare le transazioni")

                        except Exception as e:
                            st.error(f"❌ Errore nel salvataggio: {str(e)}")


def show_categories_page():
    """Pagina gestione categorie"""
    st.title("🏷️ Gestisci Categorie")

    tabs = st.tabs(["📋 Visualizza Categorie", "➕ Aggiungi/Modifica Categoria", "✏️ Modifica Budget", "🔄 Ricategorizza"])

    categories = db.get_categories()

    with tabs[0]:
        st.subheader("Categorie Esistenti")

        if len(categories) > 0:
            # Mostra categorie in card
            for _, cat in categories.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

                    with col1:
                        # Supporta sia emoji che Font Awesome
                        if cat['icon'].startswith('fa-'):
                            icon_html = render_icon_html(cat['icon'], cat['color'], '48px')
                            st.markdown(icon_html, unsafe_allow_html=True)
                        else:
                            st.markdown(f"<h1>{cat['icon']}</h1>", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**{cat['name']}**")

                    with col3:
                        st.markdown(f"Budget: **{format_currency_ita(cat['budget'])}**/mese")

                    with col4:
                        if st.button("🗑️", key=f"del_{cat['name']}", help="Elimina categoria"):
                            if cat['name'] not in ['Non Categorizzato']:
                                db.delete_category(cat['name'])
                                st.rerun()

                    st.divider()

    with tabs[1]:
        st.subheader("Aggiungi Nuova o Modifica Categoria Esistente")

        # Selettore modalità: Aggiungi o Modifica
        mode = st.radio(
            "Modalità",
            ["➕ Aggiungi Nuova", "✏️ Modifica Esistente"],
            horizontal=True,
            key="add_edit_mode"
        )

        # Inizializza variabili per entrambe le modalità
        new_name = ""
        new_budget = 0.0
        new_color = "#FF6B6B"
        cat_data = None

        if mode == "✏️ Modifica Esistente":
            # Selezione categoria da modificare
            category_to_edit = st.selectbox(
                "Seleziona Categoria da Modificare",
                options=categories['name'].tolist(),
                key="edit_cat_selector"
            )

            # Salva in session_state per accesso successivo
            st.session_state['category_to_edit'] = category_to_edit

            # Carica dati categoria selezionata
            cat_data = categories[categories['name'] == category_to_edit].iloc[0]

            st.info(f"Stai modificando: **{cat_data['name']}**")

            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Nuovo Nome Categoria", value=cat_data['name'], placeholder="es. Bollette", key="edit_name")
                new_budget = st.number_input("Budget Mensile (€)", min_value=0.0, value=float(cat_data['budget']), step=10.0, key="edit_budget")

            with col2:
                new_color = st.color_picker("Colore", value=cat_data['color'], key="edit_color")

        else:  # Aggiungi Nuova
            # In modalità aggiungi, resetta la categoria da editare
            st.session_state['category_to_edit'] = None

            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Nome Categoria", placeholder="es. Bollette", key="add_name")
                new_budget = st.number_input("Budget Mensile (€)", min_value=0.0, value=100.0, step=10.0, key="add_budget")

            with col2:
                new_color = st.color_picker("Colore", "#FF6B6B", key="add_color")

        # Selector icone Font Awesome con preview
        st.subheader("🎨 Seleziona Icona")

        # In modalità modifica, mostra icona corrente
        if mode == "✏️ Modifica Esistente" and cat_data is not None:
            current_icon = cat_data['icon']
            if current_icon.startswith('fa-'):
                icon_html = render_icon_html(current_icon, cat_data['color'], '48px')
                st.markdown(f"**Icona Corrente:** {icon_html}", unsafe_allow_html=True)
            else:
                st.markdown(f"**Icona Corrente:** {current_icon}")
            st.caption(f"Codice: `{current_icon}`")
            st.divider()

        # Modalità selezione
        selection_mode = st.radio(
            "Modalità",
            ["📁 Per Categoria", "🔍 Ricerca", "😊 Emoji Classiche"],
            horizontal=True,
            key="icon_selection_mode"
        )

        # Inizializza session_state per icona selezionata
        if 'selected_icon' not in st.session_state:
            st.session_state['selected_icon'] = None

        # In modalità modifica, inizializza con icona corrente
        if mode == "✏️ Modifica Esistente" and cat_data is not None:
            if st.session_state['selected_icon'] is None:
                st.session_state['selected_icon'] = cat_data['icon']

        if selection_mode == "😊 Emoji Classiche":
            # Emoji classiche
            emoji_options = ["📦", "🛒", "🚗", "💡", "🍽️", "🛍️", "⚕️", "🎬", "🏠", "💰", "📱", "✈️", "⚡", "🍕", "🎁", "💊", "🏃", "📚", "🐾"]
            selected_emoji = st.selectbox("Emoji", emoji_options, key="emoji_selector")
            if st.button("✅ Conferma Emoji", use_container_width=True):
                st.session_state['selected_icon'] = selected_emoji
                st.rerun()

        elif selection_mode == "🔍 Ricerca":
            # Ricerca icone
            search_query = st.text_input("🔍 Cerca icona", placeholder="es. casa, auto, cibo...")

            if search_query:
                results = search_icons(search_query)

                if results:
                    st.write(f"Trovate **{len(results)}** icone")

                    # Mostra risultati con preview
                    cols = st.columns(6)
                    for idx, icon_data in enumerate(results[:30]):  # Limita a 30 risultati
                        with cols[idx % 6]:
                            icon_html = render_icon_html(icon_data['class'], new_color, '32px')
                            if st.button(f"{icon_data['name']}", key=f"search_{idx}", use_container_width=True):
                                st.session_state['selected_icon'] = icon_data['class']
                                st.rerun()
                            st.markdown(icon_html, unsafe_allow_html=True)
                            st.caption(icon_data['name'])
                else:
                    st.info("Nessuna icona trovata. Prova con termini diversi.")
            else:
                st.info("Inserisci un termine di ricerca per trovare icone")

        else:  # Per Categoria
            # Selezione per categoria
            category_name = st.selectbox(
                "Categoria icone",
                list(ICON_LIBRARY.keys()),
                key="icon_category_selector"
            )

            icons_in_category = ICON_LIBRARY[category_name]

            st.write(f"**{len(icons_in_category)}** icone disponibili")

            # Mostra griglia icone con preview
            cols = st.columns(6)
            for idx, (icon_class, icon_name) in enumerate(icons_in_category):
                with cols[idx % 6]:
                    # Renderizza icona con colore personalizzato
                    icon_html = render_icon_html(icon_class, new_color, '32px')

                    # Bottone per selezione
                    if st.button(icon_name, key=f"icon_{idx}", use_container_width=True):
                        st.session_state['selected_icon'] = icon_class
                        st.rerun()

                    # Mostra preview icona
                    st.markdown(icon_html, unsafe_allow_html=True)

        # Usa icona da session_state
        selected_icon = st.session_state.get('selected_icon', None)

        # Mostra icona selezionata
        if selected_icon:
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Anteprima")
            with col2:
                if st.button("🔄 Cambia", key="reset_icon"):
                    st.session_state['selected_icon'] = None
                    st.rerun()

            if selected_icon.startswith('fa-'):
                # Font Awesome icon
                preview_html = render_icon_html(selected_icon, new_color, '48px')
                st.markdown(f"<div style='text-align: center; padding: 20px;'>{preview_html}</div>", unsafe_allow_html=True)
                st.info(f"✅ Icona selezionata: **{selected_icon}**")
            else:
                # Emoji
                st.markdown(f"<div style='text-align: center; font-size: 48px; padding: 20px;'>{selected_icon}</div>", unsafe_allow_html=True)
                st.info(f"✅ Emoji selezionata: **{selected_icon}**")

        # Bottone di salvataggio (Aggiungi o Modifica)
        if mode == "✏️ Modifica Esistente":
            button_label = "💾 Salva Modifiche"
            button_type = "primary"
        else:
            button_label = "➕ Aggiungi Categoria"
            button_type = "primary"

        if st.button(button_label, use_container_width=True, type=button_type):
            if new_name and selected_icon:
                if mode == "✏️ Modifica Esistente":
                    # Modifica categoria esistente
                    old_category_name = st.session_state.get('category_to_edit')
                    if not old_category_name:
                        st.error("❌ Errore: categoria da modificare non trovata")
                    else:
                        success = db.update_category(
                            old_name=old_category_name,
                            new_name=new_name,
                            new_budget=new_budget,
                            new_color=new_color,
                            new_icon=selected_icon
                        )
                        if success:
                            st.session_state['selected_icon'] = None  # Reset selezione
                            st.session_state['category_to_edit'] = None  # Reset categoria
                            st.success(f"✅ Categoria '{new_name}' aggiornata con successo!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Errore: nome categoria già esistente")
                else:
                    # Aggiungi nuova categoria
                    success = db.add_category(new_name, new_budget, new_color, selected_icon)
                    if success:
                        st.session_state['selected_icon'] = None  # Reset selezione
                        st.success(f"✅ Categoria '{new_name}' aggiunta!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Categoria già esistente")
            elif not new_name:
                st.warning("⚠️ Inserisci un nome per la categoria")
            else:
                st.warning("⚠️ Seleziona un'icona")

    with tabs[2]:
        st.subheader("Modifica Budget Categorie")

        for _, cat in categories.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Supporta sia emoji che Font Awesome
                if cat['icon'].startswith('fa-'):
                    icon_html = render_icon_html(cat['icon'], cat['color'], '24px')
                    st.markdown(f"{icon_html} **{cat['name']}**", unsafe_allow_html=True)
                else:
                    st.write(f"{cat['icon']} **{cat['name']}**")

            with col2:
                new_budget = st.number_input(
                    "Budget (€)",
                    min_value=0.0,
                    value=float(cat['budget']),
                    step=10.0,
                    key=f"budget_{cat['name']}"
                )

            with col3:
                if st.button("💾", key=f"save_{cat['name']}", help="Salva"):
                    db.update_category_budget(cat['name'], new_budget)
                    st.success("✅ Salvato!")
                    st.rerun()

    with tabs[3]:
        st.subheader("Ricategorizza Transazioni")

        transactions = db.get_all_transactions()

        if len(transactions) > 0:
            # Converti colonna date in datetime
            transactions['date'] = pd.to_datetime(transactions['date'])

            # Filtri principali
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                filter_mode = st.radio(
                    "Mostra",
                    ["Solo Non Categorizzate", "Tutte le Transazioni", "Per Categoria"],
                    horizontal=True,
                    key="recat_filter_mode"
                )

            with col2:
                if filter_mode == "Per Categoria":
                    selected_category = st.selectbox(
                        "Filtra per Categoria",
                        options=["Tutte"] + categories['name'].tolist(),
                        key="recat_category_filter"
                    )
                else:
                    selected_category = None

            with col3:
                st.write("")  # Spacer

            # Filtri aggiuntivi
            with st.expander("🔍 Filtri Avanzati", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    # Filtro per mese
                    import locale
                    try:
                        locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
                    except:
                        try:
                            locale.setlocale(locale.LC_TIME, 'Italian_Italy.1252')
                        except:
                            pass

                    available_months = sorted(transactions['date'].dt.to_period('M').unique(), reverse=True)
                    month_options = ["Tutti i mesi"] + [pd.Timestamp(m.to_timestamp()).strftime('%B %Y') for m in available_months]
                    selected_month = st.selectbox(
                        "Filtra per Mese",
                        options=month_options,
                        key="recat_month_filter"
                    )

                with col2:
                    # Filtro per ricerca testo
                    search_text = st.text_input(
                        "🔍 Cerca nella descrizione",
                        placeholder="es. supermercato, amazon...",
                        key="recat_search"
                    )

            # Applica filtro base (categoria)
            if filter_mode == "Solo Non Categorizzate":
                filtered_transactions = transactions[transactions['category'] == 'Non Categorizzato'].copy()
            elif filter_mode == "Per Categoria":
                if selected_category and selected_category != "Tutte":
                    filtered_transactions = transactions[transactions['category'] == selected_category].copy()
                else:
                    filtered_transactions = transactions.copy()
            else:  # Tutte le Transazioni
                filtered_transactions = transactions.copy()

            # Applica filtro mese
            if selected_month != "Tutti i mesi":
                # Trova il periodo corrispondente
                selected_period_str = selected_month
                for period in available_months:
                    if pd.Timestamp(period.to_timestamp()).strftime('%B %Y') == selected_period_str:
                        filtered_transactions = filtered_transactions[
                            filtered_transactions['date'].dt.to_period('M') == period
                        ]
                        break

            # Applica filtro ricerca testo
            if search_text:
                filtered_transactions = filtered_transactions[
                    filtered_transactions['description'].str.contains(search_text, case=False, na=False)
                ]

            # Ordinamento
            sort_col1, sort_col2 = st.columns([3, 1])
            with sort_col1:
                st.write("")  # Spacer
            with sort_col2:
                sort_order = st.selectbox(
                    "Ordina per",
                    ["Data (recenti prima)", "Data (vecchie prima)", "Importo (decrescente)", "Importo (crescente)"],
                    key="recat_sort",
                    label_visibility="collapsed"
                )

            # Applica ordinamento
            if sort_order == "Data (recenti prima)":
                filtered_transactions = filtered_transactions.sort_values('date', ascending=False)
            elif sort_order == "Data (vecchie prima)":
                filtered_transactions = filtered_transactions.sort_values('date', ascending=True)
            elif sort_order == "Importo (decrescente)":
                filtered_transactions = filtered_transactions.sort_values('amount', ascending=False)
            else:  # Importo (crescente)
                filtered_transactions = filtered_transactions.sort_values('amount', ascending=True)

            # Mostra contatore
            if filter_mode == "Solo Non Categorizzate":
                st.write(f"Trovate **{len(filtered_transactions)}** transazioni non categorizzate")
            elif filter_mode == "Per Categoria" and selected_category and selected_category != "Tutte":
                st.write(f"Trovate **{len(filtered_transactions)}** transazioni in categoria **{selected_category}**")
            else:
                st.write(f"Totale **{len(filtered_transactions)}** transazioni")

            if len(filtered_transactions) > 0:
                st.info("💡 **Sistema di Apprendimento Attivo**: Quando categorizzi una transazione, l'app ricorderà automaticamente:\n"
                       "- **Spese**: merchant/negozio per categorizzazione futura\n"
                       "- **Entrate**: pattern descrizione per riconoscere entrate simili")

                # Mostra le prime 50 transazioni filtrate
                display_count = min(len(filtered_transactions), 50)
                if len(filtered_transactions) > 50:
                    st.caption(f"Mostrate prime {display_count} di {len(filtered_transactions)} transazioni")

                for idx, row in filtered_transactions.head(50).iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])

                        with col1:
                            st.write(f"**{row['description']}**")

                            # Estrai e mostra merchant se rilevato
                            merchant = extract_merchant(row['description'])
                            if merchant:
                                st.caption(f"🏪 Merchant: **{merchant}**")
                            st.caption(f"{row['date']} - {format_currency_ita(row['amount'])}")

                        with col2:
                            new_cat = st.selectbox(
                                "Categoria",
                                options=categories['name'].tolist(),
                                key=f"cat_{row['id']}",
                                label_visibility="collapsed"
                            )

                        with col3:
                            if st.button("💾", key=f"save_cat_{row['id']}", help="Salva"):
                                # Aggiorna categoria transazione
                                db.update_transaction_category(row['id'], new_cat)

                                # Determina se è entrata o spesa
                                income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso',
                                                    'Sussidi', 'Investimenti', 'Altro Reddito']
                                is_income = new_cat in income_categories

                                if is_income:
                                    # Per ENTRATE: salva pattern descrizione
                                    db.save_income_pattern(row['description'], new_cat)
                                    st.success(f"✅ Salvato! L'app ricorderà questo pattern → {new_cat}")
                                else:
                                    # Per SPESE: impara associazione merchant -> categoria
                                    merchant = extract_merchant(row['description'])
                                    if merchant:
                                        db.learn_merchant_category(merchant, new_cat)
                                        st.success(f"✅ Salvato! L'app ricorderà **{merchant}** → {new_cat}")
                                    else:
                                        st.success("✅ Categoria aggiornata")

                                st.rerun()

                        st.divider()
            else:
                st.success("🎉 Tutte le transazioni sono categorizzate!")

        # Sezione gestione merchant appresi
        st.subheader("🧠 Merchant Appresi")
        learned = db.get_all_learned_merchants()

        if len(learned) > 0:
            st.write(f"L'app ha memorizzato **{len(learned)}** associazioni merchant → categoria")

            # Mostra in formato tabella
            learned_df = pd.DataFrame(learned)
            learned_df = learned_df.sort_values('usage_count', ascending=False)

            # Formatta per visualizzazione
            display_df = learned_df[['merchant', 'category', 'usage_count']].copy()
            display_df.columns = ['Merchant', 'Categoria', 'Utilizzi']

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Opzione per cancellare associazione
            with st.expander("🗑️ Gestisci Associazioni Apprese"):
                merchant_to_delete = st.selectbox(
                    "Seleziona merchant da rimuovere",
                    options=learned_df['merchant'].tolist(),
                    key="delete_merchant"
                )

                if st.button("🗑️ Rimuovi Associazione", type="secondary"):
                    db.delete_learned_merchant(merchant_to_delete)
                    st.success(f"✅ Associazione per **{merchant_to_delete}** rimossa!")
                    st.rerun()
        else:
            st.info("Nessun merchant memorizzato ancora. Inizia a categorizzare le transazioni!")


def show_recurring_expenses_page():
    """Pagina gestione spese ricorrenti"""
    st.title("💳 Spese Ricorrenti")

    st.info("""
    📋 **Gestisci le tue spese ricorrenti**

    Aggiungi spese che si ripetono regolarmente (mutuo, abbonamenti, bollette) per:
    - Monitorare i pagamenti mensili
    - Calcolare automaticamente il budget disponibile
    - Ricevere promemoria per spese in scadenza
    """)

    categories = db.get_categories()
    recurring = db.get_recurring_expenses(active_only=False)

    tabs = st.tabs(["📋 Lista Ricorrenti", "➕ Aggiungi Nuova"])

    with tabs[0]:
        st.subheader("📋 Le Tue Spese Ricorrenti")

        if len(recurring) == 0:
            st.warning("Non hai ancora aggiunto spese ricorrenti.")
            st.info("💡 Vai su **➕ Aggiungi Nuova** per creare la tua prima spesa ricorrente!")
        else:
            # Filtro attive/tutte
            show_filter = st.radio(
                "Mostra",
                options=["Attive", "Tutte"],
                horizontal=True
            )

            if show_filter == "Attive":
                recurring_filtered = recurring[recurring['active'] == 1]
            else:
                recurring_filtered = recurring

            if len(recurring_filtered) == 0:
                st.info("Nessuna spesa ricorrente attiva")
            else:
                # Mostra tabella
                for idx, row in recurring_filtered.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])

                        with col1:
                            status_icon = "🟢" if row['active'] else "🔴"
                            st.write(f"{status_icon} **{row['name']}**")
                            st.caption(f"Categoria: {row['category']}")

                        with col2:
                            st.metric("Importo", format_currency_ita(row['amount']))

                        with col3:
                            freq_map = {'mensile': '📅 Mensile', 'settimanale': '📆 Settimanale', 'annuale': '📆 Annuale'}
                            st.write(freq_map.get(row['frequency'], row['frequency']))
                            if row['frequency'] == 'mensile':
                                st.caption(f"Giorno: {row['day_of_period']}")

                        with col4:
                            # Toggle attiva/disattiva
                            new_status = st.toggle("", value=bool(row['active']), key=f"toggle_{row['id']}", label_visibility="collapsed")
                            if new_status != bool(row['active']):
                                db.toggle_recurring_expense(row['id'], new_status)
                                st.rerun()

                        with col5:
                            # Elimina
                            if st.button("🗑️", key=f"del_{row['id']}", help="Elimina"):
                                db.delete_recurring_expense(row['id'])
                                st.success(f"Eliminata: {row['name']}")
                                st.rerun()

                        # Mostra note se presenti
                        if row['notes']:
                            st.caption(f"📝 {row['notes']}")

                        st.divider()

                # Statistiche
                active_recurring = recurring[recurring['active'] == 1]
                if len(active_recurring) > 0:
                    st.subheader("📊 Riepilogo Spese Ricorrenti")

                    total_monthly = 0
                    for _, row in active_recurring.iterrows():
                        if row['frequency'] == 'mensile':
                            total_monthly += row['amount']
                        elif row['frequency'] == 'annuale':
                            total_monthly += row['amount'] / 12

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("💰 Totale Mensile Ricorrenti", format_currency_ita(total_monthly))
                    with col2:
                        st.metric("📊 Ricorrenti Attive", len(active_recurring))

    with tabs[1]:
        st.subheader("➕ Aggiungi Nuova Spesa Ricorrente")

        with st.form("add_recurring"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Nome Spesa *", placeholder="es. Mutuo, Netflix, Bolletta luce")
                category = st.selectbox("Categoria *", options=categories['name'].tolist())
                amount = st.number_input("Importo (€) *", min_value=0.01, step=0.01, format="%.2f")

            with col2:
                frequency = st.selectbox("Frequenza *", options=['mensile', 'settimanale', 'annuale'])

                if frequency == 'mensile':
                    day_of_period = st.number_input("Giorno del Mese", min_value=1, max_value=31, value=1)
                elif frequency == 'settimanale':
                    day_of_period = st.selectbox("Giorno della Settimana", options=[1, 2, 3, 4, 5, 6, 7],
                                                format_func=lambda x: ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'][x-1])
                else:
                    day_of_period = 1  # Per annuale non serve

                start_date = st.date_input("Data Inizio *", value=datetime.now())

            notes = st.text_area("Note (opzionale)", placeholder="Aggiungi dettagli aggiuntivi...")

            submitted = st.form_submit_button("💾 Salva Spesa Ricorrente", use_container_width=True, type="primary")

            if submitted:
                if not name or amount <= 0:
                    st.error("⚠️ Compila tutti i campi obbligatori!")
                else:
                    db.add_recurring_expense(
                        name=name,
                        category=category,
                        amount=amount,
                        frequency=frequency,
                        day_of_period=day_of_period,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        notes=notes
                    )
                    st.success(f"✅ Spesa ricorrente '{name}' aggiunta con successo!")
                    st.balloons()
                    st.rerun()


def show_reports_page():
    """Pagina report e analisi"""
    st.title("📊 Report & Analisi")

    transactions = db.get_all_transactions()
    categories = db.get_categories()

    if len(transactions) == 0:
        st.info("Carica delle transazioni prima di visualizzare i report")
        return

    transactions['date'] = pd.to_datetime(transactions['date'])

    # Calcola mesi disponibili per selector email report
    available_months = transactions['date'].dt.to_period('M').unique()
    available_months = [pd.Timestamp(m.to_timestamp()) for m in available_months]

    tabs = st.tabs(["📅 Report Mensile", "📈 Analisi Trend", "📧 Invia Report"])

    with tabs[0]:
        st.subheader("Report per Periodo")

        # Selettore periodo con 8 opzioni
        col1, col2 = st.columns([2, 1])

        with col1:
            period_type = st.selectbox(
                "Seleziona Periodo",
                options=[
                    "Mese Corrente",
                    "Mese Scorso",
                    "Ultimi 2 Mesi",
                    "I Trimestre (Gen-Mar)",
                    "II Trimestre (Apr-Giu)",
                    "III Trimestre (Lug-Set)",
                    "IV Trimestre (Ott-Dic)",
                    "Date Personalizzate"
                ]
            )

        # Calcola date in base al periodo selezionato
        now = datetime.now()
        current_year = now.year

        if period_type == "Mese Corrente":
            current_month = pd.Period.now('M')
            month_data = transactions[transactions['date'].dt.to_period('M') == current_month]
            period_label = current_month.strftime('%B %Y')

        elif period_type == "Mese Scorso":
            last_month = pd.Period.now('M') - 1
            month_data = transactions[transactions['date'].dt.to_period('M') == last_month]
            period_label = last_month.strftime('%B %Y')

        elif period_type == "Ultimi 2 Mesi":
            current_month = pd.Period.now('M')
            last_month = current_month - 1
            month_data = transactions[
                transactions['date'].dt.to_period('M').isin([current_month, last_month])
            ]
            period_label = f"{last_month.strftime('%B')} - {current_month.strftime('%B %Y')}"

        elif period_type == "I Trimestre (Gen-Mar)":
            start_date = pd.Timestamp(f'{current_year}-01-01')
            end_date = pd.Timestamp(f'{current_year}-03-31')
            month_data = transactions[
                (transactions['date'] >= start_date) & (transactions['date'] <= end_date)
            ]
            period_label = f"Q1 {current_year} (Gen-Mar)"

        elif period_type == "II Trimestre (Apr-Giu)":
            start_date = pd.Timestamp(f'{current_year}-04-01')
            end_date = pd.Timestamp(f'{current_year}-06-30')
            month_data = transactions[
                (transactions['date'] >= start_date) & (transactions['date'] <= end_date)
            ]
            period_label = f"Q2 {current_year} (Apr-Giu)"

        elif period_type == "III Trimestre (Lug-Set)":
            start_date = pd.Timestamp(f'{current_year}-07-01')
            end_date = pd.Timestamp(f'{current_year}-09-30')
            month_data = transactions[
                (transactions['date'] >= start_date) & (transactions['date'] <= end_date)
            ]
            period_label = f"Q3 {current_year} (Lug-Set)"

        elif period_type == "IV Trimestre (Ott-Dic)":
            start_date = pd.Timestamp(f'{current_year}-10-01')
            end_date = pd.Timestamp(f'{current_year}-12-31')
            month_data = transactions[
                (transactions['date'] >= start_date) & (transactions['date'] <= end_date)
            ]
            period_label = f"Q4 {current_year} (Ott-Dic)"

        else:  # Date Personalizzate
            with col2:
                st.caption("Seleziona range")

            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input(
                    "Data Inizio",
                    value=now - pd.Timedelta(days=30),
                    key="report_start_date"
                )
            with col_end:
                end_date = st.date_input(
                    "Data Fine",
                    value=now,
                    key="report_end_date"
                )

            start_date = pd.Timestamp(start_date)
            end_date = pd.Timestamp(end_date)

            month_data = transactions[
                (transactions['date'] >= start_date) & (transactions['date'] <= end_date)
            ]
            period_label = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

        # Mostra periodo selezionato
        st.info(f"📅 **Periodo**: {period_label} | **Transazioni**: {len(month_data)}")

        # Statistiche
        stats = calculate_spending_statistics(month_data, period='all')
        display_statistics(stats, period=period_label)

        st.divider()

        # Confronto periodi
        comparison = compare_periods(transactions)
        if comparison:
            display_period_comparison(comparison)

        st.divider()

        # Tabella dettagliata
        st.subheader("📋 Dettaglio Transazioni")
        display_df = month_data[['date', 'description', 'category', 'amount']].copy()
        display_df['date'] = display_df['date'].dt.strftime('%d/%m/%Y')
        display_df['amount'] = display_df['amount'].apply(format_currency_ita)
        display_df.columns = ['Data', 'Descrizione', 'Categoria', 'Importo']

        # Applica colori: rosso per spese, verde per entrate
        styled_df = style_transaction_amounts(display_df)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Export
        csv = month_data.to_csv(index=False)
        filename_safe = period_label.replace(' ', '_').replace('/', '-')
        st.download_button(
            "📥 Scarica Report CSV",
            csv,
            f"report_{filename_safe}.csv",
            "text/csv",
            use_container_width=True
        )

    with tabs[1]:
        st.subheader("Analisi Trend per Categoria")

        selected_cat = st.selectbox(
            "Seleziona Categoria",
            options=categories['name'].tolist()
        )

        monthly_trend, trend_text, trend_pct = category_trend_analysis(transactions, selected_cat)

        if monthly_trend is not None and len(monthly_trend) > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Trend", trend_text)

            with col2:
                st.metric("Variazione", f"{trend_pct:+.1f}%")

            # Grafico trend
            fig_trend = create_category_trend(transactions, selected_cat, months=12)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)

            # Statistiche categoria
            cat_transactions = transactions[transactions['category'] == selected_cat]
            cat_stats = calculate_spending_statistics(cat_transactions)
            display_statistics(cat_stats, period=selected_cat)

    with tabs[2]:
        st.subheader("📧 Invia Report via Email")

        recipient = st.text_input("Email Destinatario", placeholder="famiglia@example.com")

        # Seleziona periodo
        report_month = st.selectbox(
            "Periodo Report",
            options=sorted(available_months, reverse=True),
            format_func=lambda x: x.strftime('%B %Y'),
            key="report_month"
        )

        if st.button("📧 Invia Report", use_container_width=True, type="primary"):
            if recipient:
                with st.spinner("Preparazione e invio report..."):
                    # Prepara dati report
                    month_data = transactions[transactions['date'].dt.to_period('M') == report_month]

                    top_cats = month_data.groupby('category')['amount'].sum().sort_values(ascending=False).head(5)
                    top_cats_html = "<div>"
                    for cat, amount in top_cats.items():
                        top_cats_html += f'<div class="category-item"><span>{cat}</span><span>{format_currency_ita(amount)}</span></div>'
                    top_cats_html += "</div>"

                    alerts = check_budget_alerts(month_data, categories, report_month)

                    report_data = {
                        'month': report_month.strftime('%B %Y'),
                        'total': month_data['amount'].sum(),
                        'transaction_count': len(month_data),
                        'daily_average': month_data['amount'].sum() / 30,
                        'top_categories_html': top_cats_html,
                        'recommendations': '<p>Continua a monitorare le tue spese!</p>',
                        'alerts': alerts
                    }

                    if send_monthly_report(recipient, report_data):
                        st.success("✅ Report inviato con successo!")
                    else:
                        st.error("❌ Errore nell'invio. Verifica la configurazione email nelle Impostazioni.")
            else:
                st.warning("Inserisci un indirizzo email")


def show_forecasting_page():
    """Pagina previsioni"""
    st.title("🔮 Previsioni & Trend")

    transactions = db.get_all_transactions()

    if len(transactions) == 0:
        st.info("Carica delle transazioni prima di visualizzare le previsioni")
        return

    transactions['date'] = pd.to_datetime(transactions['date'])

    # Serve almeno 6 mesi di dati
    if len(transactions['date'].dt.to_period('M').unique()) < 6:
        st.warning("⚠️ Servono almeno 6 mesi di dati per previsioni affidabili")
        st.info(f"Hai dati per {len(transactions['date'].dt.to_period('M').unique())} mesi")
        return

    # Previsioni
    st.subheader("📈 Previsione Spese Future")

    col1, col2 = st.columns(2)

    with col1:
        periods = st.slider("Mesi di storico da usare", 3, 12, 6)

    with col2:
        forecast_months = st.slider("Mesi da prevedere", 1, 6, 3)

    historical, forecast_dates, forecast_values = simple_moving_average_forecast(
        transactions,
        periods=periods,
        forecast_months=forecast_months
    )

    if historical is not None:
        fig_forecast = plot_forecast(historical, forecast_dates, forecast_values)
        if fig_forecast:
            st.plotly_chart(fig_forecast, use_container_width=True)

        # Mostra previsioni in tabella
        st.subheader("📅 Previsioni Dettagliate")

        forecast_df = pd.DataFrame({
            'Mese': [d.strftime('%B %Y') for d in forecast_dates],
            'Spesa Prevista': [format_currency_ita(v) for v in forecast_values]
        })

        st.dataframe(forecast_df, use_container_width=True, hide_index=True)

        # Raccomandazioni
        if forecast_values[0] > historical.mean():
            st.warning(f"⚠️ La previsione ({format_currency_ita(forecast_values[0])}) è superiore alla media storica ({format_currency_ita(historical.mean())})")
        else:
            st.success(f"✅ La previsione ({format_currency_ita(forecast_values[0])}) è in linea con la media storica")

    # Confronti
    st.divider()
    comparison = compare_periods(transactions)
    if comparison:
        display_period_comparison(comparison)

    # Raccomandazioni budget
    st.divider()
    categories = db.get_categories()
    alerts = check_budget_alerts(transactions, categories)
    recommendations = get_budget_recommendations(alerts)
    display_recommendations(recommendations)


def show_settings_page():
    """Pagina impostazioni"""
    st.title("⚙️ Impostazioni")

    tabs = st.tabs(["💾 Backup & Ripristino", "📧 Email", "🗑️ Database", "ℹ️ Informazioni"])

    with tabs[0]:
        st.subheader("💾 Backup & Ripristino")

        transactions = db.get_all_transactions()
        categories = db.get_categories()

        # Sezione Backup
        st.markdown("### 📥 Crea Backup Completo")

        st.info(f"""
        📊 **Contenuto Database:**
        - {len(transactions)} transazioni
        - {len(categories)} categorie
        - Merchant appresi e impostazioni

        Il backup include TUTTI i tuoi dati in formato ZIP sicuro.
        """)

        if len(transactions) > 0:
            col1, col2 = st.columns(2)

            with col1:
                # Backup completo ZIP
                if st.button("📦 Scarica Backup Completo (ZIP)", use_container_width=True, type="primary"):
                    with st.spinner("Creazione backup in corso..."):
                        zip_buffer = create_full_backup(db)

                        st.download_button(
                            "⬇️ Download Backup ZIP",
                            zip_buffer,
                            get_backup_filename(),
                            "application/zip",
                            use_container_width=True
                        )
                        st.success("✅ Backup pronto! Salvalo su Dropbox, Drive o disco locale")

                        # Salva timestamp ultimo backup
                        st.session_state['last_backup'] = datetime.now()

            with col2:
                # Backup CSV semplice (legacy)
                csv_backup = transactions.to_csv(index=False)
                st.download_button(
                    "📄 Backup Solo Transazioni (CSV)",
                    csv_backup,
                    f"backup_spese_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True,
                    help="Solo transazioni, senza categorie e impostazioni"
                )

        st.divider()

        # Sezione Ripristino
        st.markdown("### ⬆️ Ripristina da Backup")

        st.warning("""
        ⚠️ **Attenzione**: Il ripristino sovrascriverà i dati esistenti.
        Scarica un backup prima di procedere!
        """)

        uploaded_backup = st.file_uploader(
            "Carica file backup (ZIP)",
            type=['zip'],
            help="Seleziona il file backup.zip scaricato precedentemente"
        )

        if uploaded_backup:
            # Mostra info sul backup
            backup_info = extract_backup_info(uploaded_backup)

            if backup_info:
                st.success("✅ Backup valido trovato!")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("📅 Data Backup", backup_info['metadata'].get('backup_date', 'N/A')[:10])
                    st.metric("📊 Transazioni", backup_info['files'].get('transactions', 0))

                with col2:
                    st.metric("🏷️ Categorie", backup_info['files'].get('categories', 0))
                    st.metric("🏪 Merchant", backup_info['files'].get('merchants', 0))

                st.divider()

                # Scegli modalità ripristino
                restore_mode = st.radio(
                    "Modalità Ripristino",
                    options=['replace', 'merge'],
                    format_func=lambda x: "🔄 Sostituisci Tutto (cancella DB e ripristina)" if x == 'replace' else "➕ Aggiungi Solo Nuovi Dati (merge intelligente)",
                    help="Replace: cancella tutto e ripristina dal backup. Merge: aggiunge solo dati nuovi, evita duplicati."
                )

                # Conferma ripristino
                if restore_mode == 'replace':
                    confirm_text = st.text_input("⚠️ Scrivi 'RIPRISTINA' per confermare la sostituzione completa")
                    confirm_ok = confirm_text == 'RIPRISTINA'
                else:
                    confirm_ok = True

                if st.button("⬆️ Avvia Ripristino", type="primary", disabled=not confirm_ok):
                    with st.spinner("Ripristino in corso..."):
                        # Reset uploaded file position
                        uploaded_backup.seek(0)
                        stats = restore_backup(uploaded_backup, db, mode=restore_mode)

                        if stats:
                            st.success("✅ Ripristino completato con successo!")
                            st.balloons()

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Transazioni", f"+{stats['transactions']}")
                            with col2:
                                st.metric("Categorie", f"+{stats['categories']}")
                            with col3:
                                st.metric("Merchant", f"+{stats['merchants']}")

                            st.info("🔄 Ricarica la pagina per vedere i dati ripristinati")

    with tabs[1]:
        configure_email_settings()

    with tabs[2]:
        st.subheader("🗑️ Gestione Database")

        transactions = db.get_all_transactions()
        st.info(f"📊 Database contiene **{len(transactions)}** transazioni")

        st.divider()

        # Reset database (attenzione!)
        with st.expander("⚠️ Zona Pericolosa"):
            st.warning("""
            **Attenzione!** Questa azione eliminerà TUTTI i dati.

            È consigliato scaricare un backup prima di procedere.
            """)

            confirm = st.text_input("Scrivi 'ELIMINA' per confermare")

            if st.button("🗑️ Elimina Tutti i Dati", type="secondary"):
                if confirm == "ELIMINA":
                    # Elimina tutte le transazioni
                    conn = db._get_conn()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions")
                    conn.commit()
                    conn.close()

                    st.success("✅ Database resettato")
                    st.rerun()
                else:
                    st.error("Conferma non corretta")

    with tabs[3]:
        st.subheader("ℹ️ Informazioni App")

        st.markdown("""
        ### 💰 Family Expense Tracker

        **Versione:** 2.0.0

        **Caratteristiche:**
        - ✅ Importazione CSV automatica
        - ✅ Categorizzazione intelligente
        - ✅ Budget mensili con alert
        - ✅ Dashboard interattiva
        - ✅ Grafici e statistiche
        - ✅ Previsioni future
        - ✅ Report via email
        - ✅ Completamente mobile-friendly
        - ✅ 100% gratuito

        **Tecnologie:**
        - Python + Streamlit
        - PostgreSQL (Supabase)
        - Plotly Charts
        - Pandas Data Analysis

        ---

        **Come Iniziare:**

        1. **Carica Dati**: Vai su "📤 Carica Dati" e importa il CSV dalla tua banca
        2. **Categorizza**: Assegna categorie alle transazioni in "🏷️ Gestisci Categorie"
        3. **Imposta Budget**: Configura i budget mensili per categoria
        4. **Monitora**: Controlla la dashboard per alert e statistiche
        5. **Analizza**: Usa report e previsioni per ottimizzare le spese

        ---

        **Supporto:**

        Per domande o problemi, consulta la sezione ❓ Guida nel menu laterale.

        **Made with ❤️ for families**
        """)


def show_help_page():
    """Pagina guida completa dell'app"""
    st.title("❓ Guida all'Uso")

    st.info("Espandi le sezioni per leggere la guida dettagliata di ogni funzione.")

    # ── GUIDA RAPIDA ──────────────────────────────────────────────────────────
    with st.expander("🚀 Guida Rapida — Inizia in 5 minuti", expanded=True):
        st.markdown("""
        ### Come iniziare

        1. **Carica il tuo CSV bancario** → vai su *📤 Carica Dati* e importa l'estratto conto della tua banca.
        2. **Rivedi le categorie** → l'app assegna automaticamente una categoria a ogni transazione. Correggila se necessario in *🏷️ Gestisci Categorie*.
        3. **Imposta i budget mensili** → in *🏷️ Gestisci Categorie* inserisci quanto vuoi spendere al mese per ogni voce (es. Alimentari €500).
        4. **Monitora la Dashboard** → ogni giorno controlla il riepilogo, il budget disponibile e gli alert.
        5. **Aggiungi le spese ricorrenti** → in *💳 Spese Ricorrenti* inserisci abbonamenti e bollette fisse così vengono detratti automaticamente dal budget disponibile.

        ---

        ### Formato CSV accettato

        L'app accetta i CSV esportati dalle principali banche italiane. Il file deve contenere almeno queste colonne (i nomi possono variare, l'app le riconosce automaticamente):

        | Colonna | Descrizione |
        |---|---|
        | Data | Data della transazione (es. `25/01/2025` o `2025-01-25`) |
        | Descrizione / Causale | Testo del movimento |
        | Importo / Dare / Avere | Valore in euro |
        | Categoria (opzionale) | Categoria già assegnata dalla banca |

        > **Tip**: Se la tua banca esporta Dare e Avere separati, l'app li unifica automaticamente in un unico campo Importo.
        """)

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    with st.expander("🏠 Dashboard"):
        st.markdown("""
        La Dashboard è la schermata principale. Si aggiorna automaticamente ogni volta che aggiungi dati.

        ### Metriche in alto
        | Metrica | Cosa mostra |
        |---|---|
        | **Spesa Mese Corrente** | Totale speso nel mese in corso |
        | **Transazioni Mese** | Numero di movimenti nel mese corrente |
        | **Media Transazione** | Importo medio per singola spesa |
        | **Media Giornaliera** | Spesa media giornaliera dall'inizio del mese |

        ### Budget Disponibile
        Mostra quanto puoi ancora spendere fino a fine mese, calcolato così:

        ```
        Disponibile = Budget Totale − Speso fino a oggi − Spese Ricorrenti ancora da pagare
        ```

        - 🟢 **Verde**: budget ampiamente disponibile
        - 🟠 **Arancione**: meno del 10% del budget rimanente
        - 🔴 **Rosso**: budget superato

        Espandi *"Dettaglio Calcolo"* per vedere la formula applicata e la spesa giornaliera consigliata per i giorni rimanenti.

        ### Spese Ricorrenti
        Mostra quante spese ricorrenti del mese sono già state pagate (✅) e quante sono ancora in attesa (⏳). Il totale mensile è calcolato includendo anche le spese annuali ripartite su 12 mesi.

        ### Alert Budget
        Appare solo se una o più categorie hanno superato le soglie di attenzione:
        - ⚡ **75%** del budget → avviso giallo
        - ⚠️ **90%** del budget → alert arancione
        - 🚨 **100%** del budget → alert rosso (budget sforato)

        ### Grafici
        - **Andamento mensile**: confronto spese mese per mese
        - **Ripartizione categorie**: grafico a torta con la distribuzione delle spese
        - **Budget vs Reale**: barre affiancate per ogni categoria
        """)

    # ── CARICA DATI ───────────────────────────────────────────────────────────
    with st.expander("📤 Carica Dati"):
        st.markdown("""
        ### Importazione CSV
        1. Esporta il file CSV dall'home banking della tua banca
        2. Caricalo nella sezione "Carica File CSV"
        3. L'app mostra un'anteprima delle prime righe: verifica che le colonne siano corrette
        4. Clicca **"Importa Transazioni"** per salvare nel database

        L'app rileva automaticamente i duplicati: se carichi due volte lo stesso CSV, le transazioni già presenti non vengono reimportate.

        ### Categorizzazione Automatica
        Ogni transazione viene analizzata e assegnata a una categoria in base a:
        - **Pattern nel testo**: "ESSELUNGA", "COOP", "LIDL" → *Alimentari*; "ENI", "IP", "AGIP" → *Trasporti*; ecc.
        - **Merchant appresi**: se hai già categorizzato manualmente una spesa da "NETFLIX", la prossima volta viene assegnata automaticamente a *Svago*
        - **Entrate**: importi positivi vengono assegnati alla categoria *Entrate*

        ### Correzione Categorie
        Dopo l'importazione, puoi correggere le categorie nella tabella. L'app impara dalla correzione e la applicherà automaticamente nelle importazioni future dallo stesso merchant.

        ### Aggiunta Manuale
        Puoi aggiungere singole transazioni manualmente (contanti, pagamenti non tracciati) usando il form nella sezione "Aggiungi Transazione Manuale".
        """)

    # ── CATEGORIE ─────────────────────────────────────────────────────────────
    with st.expander("🏷️ Gestisci Categorie"):
        st.markdown("""
        ### Categorie di Default
        Al primo avvio l'app crea automaticamente 11 categorie predefinite con budget suggeriti:

        | Categoria | Budget Default |
        |---|---|
        | Alimentari | €500/mese |
        | Trasporti | €200/mese |
        | Utenze | €300/mese |
        | Ristoranti | €250/mese |
        | Shopping | €200/mese |
        | Salute | €150/mese |
        | Svago | €150/mese |
        | Casa | €400/mese |
        | Entrate | — (nessun budget) |
        | Altro | €100/mese |
        | Non Categorizzato | — |

        ### Impostare i Budget
        Per ogni categoria puoi definire un budget mensile massimo. Questo valore viene usato per:
        - Calcolare il **budget disponibile** in Dashboard
        - Generare gli **alert** quando ti avvicini al limite
        - Produrre i grafici **Budget vs Reale** nei Report

        ### Creare Nuove Categorie
        Usa il pulsante **"Aggiungi Categoria"** per creare categorie personalizzate (es. *Viaggi*, *Sport*, *Animali*). Per ogni categoria scegli:
        - **Nome**: identificativo univoco
        - **Budget mensile**: importo massimo (0 = nessun limite)
        - **Colore**: usato nei grafici
        - **Icona**: scegli tra centinaia di icone Font Awesome

        ### Assegnare Transazioni
        Dalla lista transazioni puoi cambiare la categoria di un movimento con un menu a tendina. La modifica viene salvata immediatamente.
        """)

    # ── SPESE RICORRENTI ──────────────────────────────────────────────────────
    with st.expander("💳 Spese Ricorrenti"):
        st.markdown("""
        Le spese ricorrenti sono costi fissi che si ripetono regolarmente: affitto, abbonamenti, bollette, rate.

        ### Frequenze Supportate
        | Frequenza | Comportamento |
        |---|---|
        | **Mensile** | Si ripete ogni mese nel giorno specificato |
        | **Settimanale** | Si ripete ogni settimana |
        | **Annuale** | Si ripete una volta l'anno (es. assicurazione auto) |

        ### Come Funziona il Tracking
        L'app confronta le spese ricorrenti configurate con le transazioni importate nel mese corrente:
        - ✅ **Pagata**: trovata una transazione corrispondente nel mese
        - ⏳ **In attesa**: non ancora trovata nel CSV del mese corrente

        Le spese ricorrenti **in attesa** vengono sottratte dal budget disponibile in Dashboard, così sai già quanto ti rimarrà dopo averle pagate.

        ### Tip
        Per le spese annuali (es. bollo auto €200 a marzo), l'app le include nel calcolo del budget disponibile solo nel mese in cui cadono. Nel conteggio del totale mensile ricorrente vengono divise per 12 per mostrare il costo medio mensile.
        """)

    # ── REPORT & ANALISI ──────────────────────────────────────────────────────
    with st.expander("📊 Report & Analisi"):
        st.markdown("""
        La sezione Report offre analisi approfondite con filtri temporali.

        ### Filtri Disponibili
        - **Mese corrente / Mese precedente**
        - **Ultimi 3 mesi / Ultimo anno**
        - **Periodo personalizzato**: scegli data inizio e fine liberamente

        ### Grafici Disponibili
        | Grafico | Descrizione |
        |---|---|
        | **Andamento Mensile** | Spese totali mese per mese, con trend |
        | **Ripartizione Categorie** | Torta con percentuale per categoria |
        | **Budget vs Reale** | Barre affiancate: quanto hai speso vs quanto avevi pianificato |
        | **Entrate vs Uscite** | Saldo mensile: entrate in verde, uscite in rosso |
        | **Top Spese** | Le 10 transazioni più costose del periodo |
        | **Trend Categoria** | Evoluzione nel tempo di una singola categoria |

        ### Anomalie
        L'app rileva automaticamente le transazioni anomale rispetto alla tua media storica. Una spesa è segnalata come anomala se supera significativamente il valore tipico per quella categoria.

        ### Export via Email
        Nella sezione *Report* puoi inviare un report mensile completo via email. Il report include:
        - Totale speso, numero transazioni, media giornaliera
        - Top categorie
        - Alert budget attivi
        - Consigli personalizzati

        > Per usare questa funzione devi configurare Gmail in *⚙️ Impostazioni → Email*.
        """)

    # ── PREVISIONI ────────────────────────────────────────────────────────────
    with st.expander("🔮 Previsioni"):
        st.markdown("""
        La sezione Previsioni analizza il tuo storico per stimare le spese future.

        ### Media Mobile
        Usa la **media mobile** degli ultimi N mesi per proiettare la spesa del mese corrente e di quelli futuri. Più mesi includi nella media, più la previsione è "stabile" ma meno reattiva ai cambiamenti recenti.

        ### Statistiche Storiche
        Per ogni categoria vengono calcolate:
        - **Media mensile**: spesa tipica al mese
        - **Deviazione standard**: quanto varia la spesa
        - **Minimo / Massimo**: i mesi migliori e peggiori
        - **Trend**: la spesa sta aumentando o diminuendo nel tempo?

        ### Confronto Periodi
        Confronta due periodi diversi (es. *Gennaio-Giugno 2024* vs *Gennaio-Giugno 2025*) per vedere dove hai migliorato e dove hai speso di più.

        ### Quando le previsioni sono attendibili?
        Le previsioni funzionano meglio con almeno **3-6 mesi** di dati storici. Con meno dati, i valori sono indicativi.
        """)

    # ── IMPOSTAZIONI ──────────────────────────────────────────────────────────
    with st.expander("⚙️ Impostazioni"):
        st.markdown("""
        ### Backup & Ripristino
        È consigliato fare un backup periodico (almeno una volta al mese).

        - **Backup ZIP**: include tutte le tabelle (transazioni, categorie, merchant appresi, impostazioni). Salva il file su Google Drive, Dropbox o il tuo PC.
        - **Backup CSV**: solo le transazioni, in formato leggibile da Excel.
        - **Ripristino — Sostituisci tutto**: cancella il database e lo ricrea dal backup. Utile se vuoi tornare a uno stato precedente.
        - **Ripristino — Merge**: aggiunge solo le transazioni non ancora presenti, senza cancellare quelle esistenti. Utile per unire dati da dispositivi diversi.

        ### Email
        Per ricevere report e alert via email configura un account Gmail:
        1. Attiva la *Verifica in 2 passaggi* su [myaccount.google.com/security](https://myaccount.google.com/security)
        2. Vai su *Password per le app* e genera una password per "Mail"
        3. Inserisci email e password nell'apposita sezione

        Usa il pulsante **"Invia Email di Test"** per verificare che la configurazione funzioni.

        ### Database
        Nella *Zona Pericolosa* puoi eliminare tutte le transazioni (le categorie e le impostazioni vengono mantenute). Questa operazione è irreversibile: scarica sempre un backup prima.
        """)

    # ── FAQ ───────────────────────────────────────────────────────────────────
    with st.expander("❓ Domande Frequenti"):
        st.markdown("""
        **Posso caricare CSV di banche diverse?**
        Sì. L'app riconosce automaticamente i formati di Fineco, Intesa Sanpaolo, UniCredit, BancoBPM, Poste Italiane e molte altre. Se il formato non viene riconosciuto, controlla che il CSV abbia almeno le colonne Data, Descrizione e Importo.

        ---

        **Le mie categorie vengono perse se cancello le transazioni?**
        No. Le categorie e le loro impostazioni sono memorizzate separatamente dalle transazioni. Cancellare le transazioni non tocca le categorie, i budget o i merchant appresi.

        ---

        **Posso usare l'app in famiglia con più persone?**
        Attualmente l'app ha un unico database condiviso. Tutti gli utenti che accedono allo stesso URL vedono e modificano gli stessi dati. È pensata per un nucleo familiare che condivide le spese.

        ---

        **I dati sono al sicuro?**
        I dati sono salvati su Supabase (PostgreSQL cloud, data center in Europa). La connessione è cifrata (SSL). Solo chi ha l'URL dell'app può accedere ai dati.

        ---

        **L'app funziona offline?**
        No, richiede una connessione internet per comunicare con il database cloud.

        ---

        **Come faccio a spostare i dati se cambio account?**
        Fai un backup ZIP da *⚙️ Impostazioni → Backup*, poi ripristinalo sulla nuova istanza con la modalità "Sostituisci tutto".

        ---

        **Perché alcune transazioni vanno in "Non Categorizzato"?**
        L'app non ha riconosciuto il merchant o il testo della transazione. Vai in *🏷️ Gestisci Categorie*, assegna manualmente la categoria corretta: l'app imparerà per le importazioni future.
        """)


if __name__ == "__main__":
    main()
