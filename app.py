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

    # Alert Budget
    alerts = check_budget_alerts(transactions, categories, current_month)
    if alerts:
        summary = create_budget_summary_card(alerts)
        display_budget_summary(summary)
        st.divider()
        display_alerts(alerts, show_all=False)
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
                            db.insert_transactions(df)
                            st.success(f"✅ {len(df)} transazioni salvate con successo!")
                            st.balloons()

                            # Suggerisci di categorizzare
                            if not auto_categorize:
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

    tabs = st.tabs(["📧 Email", "💾 Database", "ℹ️ Informazioni"])

    with tabs[0]:
        configure_email_settings()

    with tabs[1]:
        st.subheader("💾 Gestione Database")

        transactions = db.get_all_transactions()

        st.info(f"📊 Database contiene **{len(transactions)}** transazioni")

        # Backup
        if len(transactions) > 0:
            csv_backup = transactions.to_csv(index=False)
            st.download_button(
                "📥 Scarica Backup Database (CSV)",
                csv_backup,
                f"backup_spese_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

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
