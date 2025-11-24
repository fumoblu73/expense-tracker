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
        hovermode='x unified'
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_daily_spending_trend(df, days=30):
    """Crea grafico andamento spese giornaliere"""
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Ultimi N giorni
    latest_date = df_copy['date'].max()
    start_date = latest_date - pd.Timedelta(days=days)
    df_filtered = df_copy[df_copy['date'] >= start_date]

    # Aggrega per giorno
    daily = df_filtered.groupby('date')['amount'].sum().sort_index()

    fig = px.line(
        x=daily.index,
        y=daily.values,
        labels={'x': 'Data', 'y': 'Spesa (€)'},
        title=f'📈 Andamento Spese Giornaliere (Ultimi {days} giorni)',
        markers=True
    )

    fig.update_traces(
        line_color='#FF6B6B',
        marker=dict(size=8),
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>€%{y:,.2f}<extra></extra>'
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='x unified'
    )

    return fig


def create_top_expenses_table(df, limit=10):
    """Crea tabella delle spese più alte (escluse le entrate)"""
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Filtra solo spese (escludi entrate)
    expenses_only = df_copy[df_copy['category'] != 'Entrate']

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
        hovermode='x unified'
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
