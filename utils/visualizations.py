"""
Modulo per la creazione di grafici e visualizzazioni
Tutti i grafici sono ottimizzati per dispositivi mobili
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.formatters import format_currency_ita


def create_monthly_summary(df):
    """Crea grafico riepilogo spese mensili"""
    if df is None or len(df) == 0:
        return None

    # Converti date
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Aggrega per mese
    monthly = df_copy.groupby(df_copy['date'].dt.to_period('M'))['amount'].sum()
    monthly.index = monthly.index.astype(str)

    fig = px.bar(
        x=monthly.index,
        y=monthly.values,
        labels={'x': 'Mese', 'y': 'Spesa Totale (€)'},
        title='📊 Andamento Spese Mensili',
        color=monthly.values,
        color_continuous_scale='Reds'
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
        hovermode='x unified',
        separators=',.'  # Formato italiano: virgola decimale, punto migliaia
    )

    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>€%{y:,.2f}<extra></extra>'
    )

    return fig


def create_category_pie(df, categories_df=None):
    """Crea grafico a torta per categorie"""
    if df is None or len(df) == 0:
        return None

    # Aggrega per categoria
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)

    # Ottieni colori dalle categorie se disponibili
    colors = None
    if categories_df is not None:
        color_map = dict(zip(categories_df['name'], categories_df['color']))
        colors = [color_map.get(cat, '#95A5A6') for cat in category_totals.index]

    fig = px.pie(
        values=category_totals.values,
        names=category_totals.index,
        title='🏷️ Spese per Categoria',
        hole=0.4,
        color_discrete_sequence=colors if colors else px.colors.qualitative.Set3
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>'
    )

    fig.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=True,
        separators=',.',  # Formato italiano: virgola decimale, punto migliaia
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )

    return fig


def create_budget_comparison(df, categories_df, month=None):
    """Confronto Budget vs Spesa Effettiva"""
    if df is None or len(df) == 0 or categories_df is None:
        return None

    # Converti date
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Filtra per mese se specificato
    if month:
        df_copy = df_copy[df_copy['date'].dt.to_period('M') == month]

    # Calcola spesa effettiva per categoria
    actual = df_copy.groupby('category')['amount'].sum()

    # Prepara dati per il confronto
    comparison_data = []
    for _, budget_row in categories_df.iterrows():
        category = budget_row['name']
        budget = budget_row['budget']

        if budget > 0:  # Mostra solo categorie con budget impostato
            spent = actual.get(category, 0)
            remaining = max(budget - spent, 0)
            overspent = max(spent - budget, 0)

            comparison_data.append({
                'Categoria': category,
                'Budget': budget,
                'Speso': spent,
                'Rimanente': remaining,
                'Sforato': overspent,
                'Percentuale': (spent / budget * 100) if budget > 0 else 0
            })

    if not comparison_data:
        return None

    comparison_df = pd.DataFrame(comparison_data)

    # Crea grafico a barre raggruppate
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Budget',
        x=comparison_df['Categoria'],
        y=comparison_df['Budget'],
        marker_color='lightblue',
        hovertemplate='<b>%{x}</b><br>Budget: €%{y:,.2f}<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        name='Speso',
        x=comparison_df['Categoria'],
        y=comparison_df['Speso'],
        marker_color=comparison_df['Percentuale'].apply(
            lambda x: '#FF4B4B' if x >= 90 else '#FFA500' if x >= 75 else '#4ECDC4'
        ),
        hovertemplate='<b>%{x}</b><br>Speso: €%{y:,.2f}<extra></extra>'
    ))

    month_str = f" - {month}" if month else ""
    fig.update_layout(
        title=f'💰 Budget vs Spesa Effettiva{month_str}',
        barmode='group',
        height=400,
        margin=dict(l=20, r=20, t=60, b=100),
        xaxis_tickangle=-45,
        hovermode='x unified',
        separators=',.',  # Formato italiano: virgola decimale, punto migliaia
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_monthly_category_vs_budget(df, categories_df, selected_category=None):
    """
    Crea grafico andamento mensile categoria vs budget

    Args:
        df: DataFrame transazioni
        categories_df: DataFrame categorie con budget
        selected_category: Categoria specifica da mostrare (None = tutte con budget)

    Returns:
        Figura Plotly
    """
    if df is None or len(df) == 0 or categories_df is None:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Categorie entrate da escludere
    income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso', 'Sussidi', 'Investimenti', 'Altro Reddito']

    # Filtra categorie con budget impostato
    categories_with_budget = categories_df[categories_df['budget'] > 0]

    if len(categories_with_budget) == 0:
        return None

    # Se specificata una categoria, filtra
    if selected_category and selected_category != "Tutte":
        categories_with_budget = categories_with_budget[categories_with_budget['name'] == selected_category]

    # Aggrega per mese e categoria
    df_copy['month'] = df_copy['date'].dt.to_period('M')
    monthly_by_cat = df_copy.groupby(['month', 'category'])['amount'].sum().reset_index()
    monthly_by_cat['month'] = monthly_by_cat['month'].astype(str)

    fig = go.Figure()

    # Per ogni categoria con budget, aggiungi traccia spesa e budget
    for _, cat in categories_with_budget.iterrows():
        cat_name = cat['name']

        # Salta categorie di entrate
        if cat_name in income_categories:
            continue

        cat_data = monthly_by_cat[monthly_by_cat['category'] == cat_name]

        if len(cat_data) == 0:
            continue

        # Linea spesa effettiva
        fig.add_trace(go.Scatter(
            x=cat_data['month'],
            y=cat_data['amount'],
            mode='lines+markers',
            name=f'{cat_name} (Spesa)',
            line=dict(width=2),
            marker=dict(size=8),
            hovertemplate=f'<b>{cat_name}</b><br>%{{x}}<br>Speso: €%{{y:,.2f}}<extra></extra>'
        ))

        # Linea budget (costante)
        fig.add_trace(go.Scatter(
            x=cat_data['month'],
            y=[cat['budget']] * len(cat_data),
            mode='lines',
            name=f'{cat_name} (Budget)',
            line=dict(dash='dash', width=2),
            hovertemplate=f'<b>{cat_name} - Budget</b><br>%{{x}}<br>Budget: €%{{y:,.2f}}<extra></extra>'
        ))

    title = f"📊 Andamento Mensile: {selected_category if selected_category and selected_category != 'Tutte' else 'Tutte le Categorie'} vs Budget"

    fig.update_layout(
        title=title,
        xaxis_title='Mese',
        yaxis_title='Importo (€)',
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='x unified',
        separators=',.',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    return fig


def create_income_vs_expenses_trend(df, months=6):
    """
    Crea grafico confronto totale entrate vs spese mensili

    Args:
        df: DataFrame transazioni
        months: Numero di mesi da mostrare (default 6)

    Returns:
        Figura Plotly
    """
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Categorie che sono ENTRATE
    income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso', 'Sussidi', 'Investimenti', 'Altro Reddito']

    # Separa entrate e spese
    df_income = df_copy[df_copy['category'].isin(income_categories)]
    df_expenses = df_copy[~df_copy['category'].isin(income_categories)]

    # Aggrega per mese
    df_copy['month'] = df_copy['date'].dt.to_period('M')
    df_income['month'] = df_income['date'].dt.to_period('M')
    df_expenses['month'] = df_expenses['date'].dt.to_period('M')

    monthly_income = df_income.groupby('month')['amount'].sum()
    monthly_expenses = df_expenses.groupby('month')['amount'].sum()

    # Prendi ultimi N mesi
    all_months = sorted(set(monthly_income.index) | set(monthly_expenses.index))
    all_months = all_months[-months:] if len(all_months) > months else all_months

    # Riempi mesi mancanti con 0
    income_values = [monthly_income.get(m, 0) for m in all_months]
    expense_values = [monthly_expenses.get(m, 0) for m in all_months]
    month_labels = [str(m) for m in all_months]

    fig = go.Figure()

    # Barra entrate (verde)
    fig.add_trace(go.Bar(
        x=month_labels,
        y=income_values,
        name='Entrate',
        marker_color='#4ECDC4',
        hovertemplate='<b>Entrate</b><br>%{x}<br>€%{y:,.2f}<extra></extra>'
    ))

    # Barra spese (rosso)
    fig.add_trace(go.Bar(
        x=month_labels,
        y=expense_values,
        name='Spese',
        marker_color='#FF6B6B',
        hovertemplate='<b>Spese</b><br>%{x}<br>€%{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        title='💰 Confronto Entrate vs Spese Mensili',
        xaxis_title='Mese',
        yaxis_title='Importo (€)',
        barmode='group',
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='x unified',
        separators=',.',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def style_transaction_amounts(df):
    """
    Applica stile colore agli importi delle transazioni
    Rosso = spese, Verde = entrate

    Args:
        df: DataFrame con colonne 'category' e 'Importo' già formattate

    Returns:
        DataFrame con styling applicato
    """
    income_categories = ['Stipendio', 'Pensione', 'Bonifico', 'Rimborso', 'Sussidi', 'Investimenti', 'Altro Reddito']

    def color_amount(row):
        if row['Categoria'] in income_categories:
            return [''] * (len(row) - 1) + ['color: #4ECDC4; font-weight: bold']  # Verde acqua per entrate
        else:
            return [''] * (len(row) - 1) + ['color: #FF6B6B; font-weight: bold']  # Rosso per spese

    return df.style.apply(color_amount, axis=1)


def create_top_expenses_table(df, limit=10):
    """
    Crea tabella delle spese più alte (escluse le entrate)

    Le entrate sono identificate da categorie come:
    Stipendio, Pensione, Bonifico, Rimborso, Sussidi, Investimenti, Altro Reddito
    """
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Categorie che sono ENTRATE (da escludere dalla top spese)
    income_categories = [
        'Stipendio', 'Pensione', 'Bonifico', 'Rimborso',
        'Sussidi', 'Investimenti', 'Altro Reddito'
    ]

    # Filtra solo spese (escludi tutte le categorie di entrate)
    expenses_only = df_copy[~df_copy['category'].isin(income_categories)]

    if len(expenses_only) == 0:
        # Se non ci sono spese, mostra messaggio
        return pd.DataFrame({
            'Data': ['---'],
            'Descrizione': ['Nessuna spesa trovata'],
            'Categoria': ['Solo entrate nel periodo'],
            'Importo': ['€0,00']
        })

    # Ordina per importo
    top_expenses = expenses_only.nlargest(limit, 'amount')[
        ['date', 'description', 'category', 'amount']
    ].copy()

    top_expenses['date'] = top_expenses['date'].dt.strftime('%d/%m/%Y')
    # Usa formato italiano: punto migliaia, virgola decimali
    top_expenses['amount'] = top_expenses['amount'].apply(format_currency_ita)

    top_expenses.columns = ['Data', 'Descrizione', 'Categoria', 'Importo']

    return top_expenses


def create_category_trend(df, category, months=6):
    """Mostra trend per una categoria specifica"""
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Filtra per categoria
    df_filtered = df_copy[df_copy['category'] == category]

    if len(df_filtered) == 0:
        return None

    # Aggrega per mese
    monthly = df_filtered.groupby(
        df_filtered['date'].dt.to_period('M')
    )['amount'].sum()

    # Prendi ultimi N mesi
    monthly = monthly.tail(months)
    monthly.index = monthly.index.astype(str)

    fig = px.area(
        x=monthly.index,
        y=monthly.values,
        labels={'x': 'Mese', 'y': 'Spesa (€)'},
        title=f'📊 Trend: {category}',
    )

    fig.update_traces(
        line_color='#4ECDC4',
        fillcolor='rgba(78, 205, 196, 0.3)',
        hovertemplate='<b>%{x}</b><br>€%{y:,.2f}<extra></extra>'
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='x unified',
        separators=',.'  # Formato italiano: virgola decimale, punto migliaia
    )

    return fig


def create_weekly_heatmap(df):
    """Mappa di calore spese per giorno della settimana"""
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Aggiungi giorno settimana
    df_copy['weekday'] = df_copy['date'].dt.day_name()
    df_copy['week'] = df_copy['date'].dt.isocalendar().week

    # Aggrega
    heatmap_data = df_copy.groupby(['week', 'weekday'])['amount'].sum().unstack(fill_value=0)

    # Ordina giorni
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=days_order, fill_value=0)

    fig = px.imshow(
        heatmap_data.T,
        labels=dict(x="Settimana", y="Giorno", color="Spesa €"),
        x=heatmap_data.index,
        y=heatmap_data.columns,
        color_continuous_scale='Reds',
        title='🔥 Mappa Calore Spese Settimanali'
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig
