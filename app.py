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
from utils.visualizations import (
    create_monthly_summary,
    create_category_pie,
    create_budget_comparison,
    create_daily_spending_trend,
    create_top_expenses_table,
    create_category_trend
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

# Configurazione pagina
st.set_page_config(
    page_title="Family Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

db = get_database()


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
                "⚙️ Impostazioni"
            ],
            label_visibility="collapsed"
        )

        st.divider()

        # Quick stats nella sidebar
        transactions = db.get_all_transactions()
        if len(transactions) > 0:
            st.metric("Totale Transazioni", len(transactions))
            st.metric("Spesa Totale", f"€{transactions['amount'].sum():,.2f}")

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
        st.metric("Spesa Mese Corrente", f"€{total_month:,.2f}")

    with col2:
        count_month = len(month_transactions)
        st.metric("Transazioni Mese", count_month)

    with col3:
        avg_transaction = month_transactions['amount'].mean() if len(month_transactions) > 0 else 0
        st.metric("Media Transazione", f"€{avg_transaction:,.2f}")

    with col4:
        days_in_month = datetime.now().day
        daily_avg = total_month / days_in_month if days_in_month > 0 else 0
        st.metric("Media Giornaliera", f"€{daily_avg:,.2f}")

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
            f"€{balance_info['available']:,.2f}",
            f"{status_text}"
        )

        # Dettaglio
        with st.expander("📊 Dettaglio Calcolo"):
            st.write(f"**Budget Totale**: €{balance_info['total_budget']:,.2f}")
            st.write(f"**Speso fino ad oggi**: -€{balance_info['spent']:,.2f}")
            st.write(f"**Spese ricorrenti da pagare**: -€{balance_info['recurring_pending']:,.2f}")
            st.write("─" * 40)
            st.write(f"**Disponibile**: €{balance_info['available']:,.2f}")

            if balance_info['days_remaining'] > 0:
                st.info(f"💡 Puoi spendere **€{balance_info['daily_allowance']:,.2f}** al giorno per i prossimi **{balance_info['days_remaining']} giorni**")

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

            st.metric("Totale Mensile", f"€{total_recurring:,.2f}")

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

    # Alert Budget
    alerts = check_budget_alerts(transactions, categories, current_month)
    if alerts:
        summary = create_budget_summary_card(alerts)
        display_budget_summary(summary)
        st.divider()
        display_alerts(alerts, show_all=False)
        st.divider()

    # Anomalie di Spesa
    anomaly_summary = get_anomaly_summary(transactions, lookback_months=3)

    if anomaly_summary['total_count'] > 0:
        st.warning(f"⚠️ **Transazioni Insolite Rilevate**: {anomaly_summary['total_count']} anomalie negli ultimi 3 mesi")

        with st.expander("📊 Mostra Dettagli Anomalie"):
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
                        st.metric("Importo", f"€{row['amount']:,.2f}")
                        st.caption(f"Media: €{row['mean_amount']:,.2f}")

                    with col3:
                        st.write(f"**+{row['deviation_pct']:.0f}%**")
                        st.caption(row['explanation'])

                if len(anomaly_summary['amount_anomalies']) > 5:
                    st.caption(f"... e altre {len(anomaly_summary['amount_anomalies']) - 5} anomalie")

            # Anomalie per frequenza
            if len(anomaly_summary['frequency_anomalies']) > 0:
                st.subheader("🔄 Merchant con Frequenza Insolita")

                for idx, row in anomaly_summary['frequency_anomalies'].head(3).iterrows():
                    st.write(f"**{row['merchant']}**: {row['transaction_count']} transazioni (€{row['total_amount']:,.2f} totale)")
                    st.caption(row['explanation'])

        st.divider()

    # Grafici principali
    col1, col2 = st.columns(2)

    with col1:
        fig_monthly = create_monthly_summary(transactions)
        if fig_monthly:
            st.plotly_chart(fig_monthly, use_container_width=True)

    with col2:
        fig_pie = create_category_pie(transactions, categories)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)

    # Budget comparison
    fig_budget = create_budget_comparison(transactions, categories, current_month)
    if fig_budget:
        st.plotly_chart(fig_budget, use_container_width=True)

    # Trend giornaliero
    fig_daily = create_daily_spending_trend(transactions, days=30)
    if fig_daily:
        st.plotly_chart(fig_daily, use_container_width=True)

    # Top spese
    st.subheader("💸 Top 10 Spese del Mese")
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
                            if saved_count > 0 and not auto_categorize:
                                st.info("💡 Vai su **🏷️ Gestisci Categorie** per categorizzare le transazioni")

                        except Exception as e:
                            st.error(f"❌ Errore nel salvataggio: {str(e)}")


def auto_categorize_transactions(df, categories_df):
    """Categorizzazione automatica semplice basata su parole chiave"""

    # Dizionario parole chiave -> categoria
    keywords = {
        'Alimentari': ['supermercato', 'conad', 'coop', 'esselunga', 'carrefour', 'lidl', 'eurospin', 'pam'],
        'Trasporti': ['benzina', 'eni', 'q8', 'ip', 'esso', 'trenitalia', 'italo', 'atm', 'bus', 'metro'],
        'Ristoranti': ['ristorante', 'pizzeria', 'bar', 'caffè', 'trattoria', 'osteria', 'mcdonald', 'burger'],
        'Utenze': ['enel', 'eni', 'gas', 'acqua', 'luce', 'telecom', 'tim', 'vodafone', 'wind'],
        'Shopping': ['amazon', 'zara', 'h&m', 'nike', 'decathlon', 'ikea', 'mediaworld'],
        'Salute': ['farmacia', 'dottore', 'medico', 'ospedale', 'clinica'],
        'Casa': ['affitto', 'condominio', 'idraulico', 'elettricista'],
        'Svago': ['cinema', 'teatro', 'palestra', 'sport', 'netflix', 'spotify']
    }

    def categorize_row(description):
        desc_lower = str(description).lower()
        for category, words in keywords.items():
            if any(word in desc_lower for word in words):
                return category
        return 'Non Categorizzato'

    df['category'] = df['description'].apply(categorize_row)
    return df


def show_categories_page():
    """Pagina gestione categorie"""
    st.title("🏷️ Gestisci Categorie")

    tabs = st.tabs(["📋 Visualizza Categorie", "➕ Aggiungi Categoria", "✏️ Modifica Budget", "🔄 Ricategorizza"])

    categories = db.get_categories()

    with tabs[0]:
        st.subheader("Categorie Esistenti")

        if len(categories) > 0:
            # Mostra categorie in card
            for _, cat in categories.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

                    with col1:
                        st.markdown(f"<h1>{cat['icon']}</h1>", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**{cat['name']}**")

                    with col3:
                        st.markdown(f"Budget: **€{cat['budget']:,.2f}**/mese")

                    with col4:
                        if st.button("🗑️", key=f"del_{cat['name']}", help="Elimina categoria"):
                            if cat['name'] not in ['Non Categorizzato']:
                                db.delete_category(cat['name'])
                                st.rerun()

                    st.divider()

    with tabs[1]:
        st.subheader("Aggiungi Nuova Categoria")

        col1, col2 = st.columns(2)

        with col1:
            new_name = st.text_input("Nome Categoria", placeholder="es. Bollette")
            new_budget = st.number_input("Budget Mensile (€)", min_value=0.0, value=100.0, step=10.0)

        with col2:
            new_icon = st.selectbox("Icona", ["📦", "🛒", "🚗", "💡", "🍽️", "🛍️", "⚕️", "🎬", "🏠", "💰", "📱", "✈️"])
            new_color = st.color_picker("Colore", "#FF6B6B")

        if st.button("➕ Aggiungi Categoria", use_container_width=True, type="primary"):
            if new_name:
                success = db.add_category(new_name, new_budget, new_color, new_icon)
                if success:
                    st.success(f"✅ Categoria '{new_name}' aggiunta!")
                    st.rerun()
                else:
                    st.error("❌ Categoria già esistente")
            else:
                st.warning("Inserisci un nome per la categoria")

    with tabs[2]:
        st.subheader("Modifica Budget Categorie")

        for _, cat in categories.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
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
            # Filtra solo non categorizzate
            uncategorized = transactions[transactions['category'] == 'Non Categorizzato']

            st.write(f"Trovate **{len(uncategorized)}** transazioni non categorizzate")

            if len(uncategorized) > 0:
                st.info("💡 **Sistema di Apprendimento Attivo**: Quando categorizzi una transazione, l'app ricorderà automaticamente il negozio/merchant per le prossime volte!")

                # Mostra le prime 20
                for idx, row in uncategorized.head(20).iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])

                        with col1:
                            st.write(f"**{row['description']}**")

                            # Estrai e mostra merchant se rilevato
                            merchant = extract_merchant(row['description'])
                            if merchant:
                                st.caption(f"🏪 Merchant: **{merchant}**")
                            st.caption(f"{row['date']} - €{row['amount']:,.2f}")

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

                                # Impara associazione merchant -> categoria
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
                            st.metric("Importo", f"€{row['amount']:,.2f}")

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
                        st.metric("💰 Totale Mensile Ricorrenti", f"€{total_monthly:,.2f}")
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

    tabs = st.tabs(["📅 Report Mensile", "📈 Analisi Trend", "📧 Invia Report"])

    with tabs[0]:
        st.subheader("Report Mensile")

        # Seleziona mese
        available_months = transactions['date'].dt.to_period('M').unique()
        selected_month = st.selectbox(
            "Seleziona Mese",
            options=sorted(available_months, reverse=True),
            format_func=lambda x: x.strftime('%B %Y')
        )

        month_data = transactions[transactions['date'].dt.to_period('M') == selected_month]

        # Statistiche
        stats = calculate_spending_statistics(month_data, period='all')
        display_statistics(stats, period=str(selected_month))

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
        display_df['amount'] = display_df['amount'].apply(lambda x: f"€{x:,.2f}")
        display_df.columns = ['Data', 'Descrizione', 'Categoria', 'Importo']

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Export
        csv = month_data.to_csv(index=False)
        st.download_button(
            "📥 Scarica Report CSV",
            csv,
            f"report_{selected_month}.csv",
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
                        top_cats_html += f'<div class="category-item"><span>{cat}</span><span>€{amount:,.2f}</span></div>'
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
            'Spesa Prevista': [f"€{v:,.2f}" for v in forecast_values]
        })

        st.dataframe(forecast_df, use_container_width=True, hide_index=True)

        # Raccomandazioni
        if forecast_values[0] > historical.mean():
            st.warning(f"⚠️ La previsione (€{forecast_values[0]:,.2f}) è superiore alla media storica (€{historical.mean():,.2f})")
        else:
            st.success(f"✅ La previsione (€{forecast_values[0]:,.2f}) è in linea con la media storica")

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
                        zip_buffer = create_full_backup(db.db_path)

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
                        stats = restore_backup(uploaded_backup, db.db_path, mode=restore_mode)

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
                    import sqlite3
                    conn = sqlite3.connect(db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions")
                    conn.commit()
                    conn.close()

                    st.success("✅ Database resettato")
                    st.rerun()
                else:
                    st.error("Conferma non corretta")

    with tabs[2]:
        st.subheader("ℹ️ Informazioni App")

        st.markdown("""
        ### 💰 Family Expense Tracker

        **Versione:** 1.0.0

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
        - SQLite Database
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

        Per domande o problemi, consulta la documentazione o contatta il supporto.

        **Made with ❤️ for families**
        """)


if __name__ == "__main__":
    main()
