"""
Modulo per previsioni e analisi trend
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def simple_moving_average_forecast(df, periods=3, forecast_months=3):
    """
    Previsione semplice basata su media mobile

    Args:
        df: DataFrame delle transazioni
        periods: Numero di mesi da usare per la media
        forecast_months: Mesi da prevedere

    Returns:
        Tuple (historical, forecast_dates, forecast_values)
    """
    if df is None or len(df) == 0:
        return None, None, None

    # Converti date
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Aggrega per mese
    monthly = df_copy.groupby(df_copy['date'].dt.to_period('M'))['amount'].sum()

    if len(monthly) < periods:
        return None, None, None

    monthly.index = monthly.index.to_timestamp()

    # Calcola media mobile
    ma = monthly.rolling(window=periods).mean()

    # Previsione = ultima media mobile
    last_value = ma.iloc[-1]
    last_date = monthly.index[-1]

    # Genera date future
    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=forecast_months,
        freq='MS'
    )

    # Previsione semplice (stessa media)
    forecast_values = [last_value] * forecast_months

    return monthly, forecast_dates, forecast_values


def plot_forecast(historical, forecast_dates, forecast_values):
    """Crea grafico con previsioni"""
    if historical is None or forecast_dates is None:
        return None

    fig = go.Figure()

    # Dati storici
    fig.add_trace(go.Scatter(
        x=historical.index,
        y=historical.values,
        mode='lines+markers',
        name='Storico',
        line=dict(color='#4ECDC4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x|%B %Y}</b><br>€%{y:,.2f}<extra></extra>'
    ))

    # Previsione
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_values,
        mode='lines+markers',
        name='Previsione',
        line=dict(color='#FF6B6B', width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond'),
        hovertemplate='<b>%{x|%B %Y}</b><br>€%{y:,.2f} (previsto)<extra></extra>'
    ))

    # Linea di connessione
    fig.add_trace(go.Scatter(
        x=[historical.index[-1], forecast_dates[0]],
        y=[historical.values[-1], forecast_values[0]],
        mode='lines',
        line=dict(color='gray', width=1, dash='dot'),
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        title='🔮 Previsione Spese Future',
        xaxis_title='Mese',
        yaxis_title='Spesa (€)',
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
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


def category_trend_analysis(df, category, min_months=3):
    """
    Analizza il trend per una categoria specifica

    Returns:
        Tuple (monthly_data, trend_text, trend_percentage)
    """
    if df is None or len(df) == 0:
        return None, "Dati insufficienti", 0

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Filtra per categoria
    category_df = df_copy[df_copy['category'] == category]

    if len(category_df) == 0:
        return None, "Nessuna transazione in questa categoria", 0

    # Aggrega per mese
    monthly = category_df.groupby(
        category_df['date'].dt.to_period('M')
    )['amount'].sum()

    if len(monthly) < min_months:
        return monthly, "Dati insufficienti per analisi trend", 0

    # Calcola trend
    first_value = monthly.iloc[0]
    last_value = monthly.iloc[-1]

    if first_value > 0:
        trend_pct = ((last_value - first_value) / first_value) * 100
    else:
        trend_pct = 0

    # Determina descrizione trend
    if trend_pct > 20:
        trend = "📈 In forte aumento"
        emoji = "⬆️"
    elif trend_pct > 5:
        trend = "📊 In leggero aumento"
        emoji = "↗️"
    elif trend_pct < -20:
        trend = "📉 In forte diminuzione"
        emoji = "⬇️"
    elif trend_pct < -5:
        trend = "📊 In leggera diminuzione"
        emoji = "↘️"
    else:
        trend = "➡️ Stabile"
        emoji = "➡️"

    trend_text = f"{emoji} {trend} ({trend_pct:+.1f}%)"

    return monthly, trend_text, trend_pct


def calculate_spending_statistics(df, period='all'):
    """
    Calcola statistiche sulle spese

    Args:
        df: DataFrame transazioni
        period: 'all', 'month', 'year'

    Returns:
        Dict con statistiche
    """
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    # Filtra per periodo
    if period == 'month':
        current_month = pd.Period.now('M')
        df_copy = df_copy[df_copy['date'].dt.to_period('M') == current_month]
    elif period == 'year':
        current_year = pd.Period.now('Y')
        df_copy = df_copy[df_copy['date'].dt.to_period('Y') == current_year]

    if len(df_copy) == 0:
        return None

    stats = {
        'total': df_copy['amount'].sum(),
        'count': len(df_copy),
        'average': df_copy['amount'].mean(),
        'median': df_copy['amount'].median(),
        'max': df_copy['amount'].max(),
        'min': df_copy['amount'].min(),
        'std': df_copy['amount'].std()
    }

    # Media giornaliera
    days = (df_copy['date'].max() - df_copy['date'].min()).days + 1
    stats['daily_average'] = stats['total'] / days if days > 0 else 0

    # Categoria più costosa
    category_totals = df_copy.groupby('category')['amount'].sum()
    if len(category_totals) > 0:
        stats['top_category'] = category_totals.idxmax()
        stats['top_category_amount'] = category_totals.max()

    return stats


def display_statistics(stats, period='all'):
    """Visualizza statistiche in card"""
    if stats is None:
        st.info("Nessun dato disponibile per questo periodo")
        return

    period_labels = {
        'all': 'Totale',
        'month': 'Questo Mese',
        'year': 'Quest\'Anno'
    }

    st.subheader(f"📊 Statistiche - {period_labels.get(period, period)}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Spesa Totale", f"€{stats['total']:,.2f}")

    with col2:
        st.metric("N° Transazioni", f"{stats['count']}")

    with col3:
        st.metric("Media per Transazione", f"€{stats['average']:,.2f}")

    with col4:
        st.metric("Media Giornaliera", f"€{stats['daily_average']:,.2f}")

    # Seconda riga
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Spesa Massima", f"€{stats['max']:,.2f}")

    with col2:
        st.metric("Spesa Minima", f"€{stats['min']:,.2f}")

    with col3:
        st.metric("Mediana", f"€{stats['median']:,.2f}")

    with col4:
        if 'top_category' in stats:
            st.metric("Top Categoria", stats['top_category'])
            st.caption(f"€{stats['top_category_amount']:,.2f}")


def compare_periods(df, category=None):
    """
    Confronta spese tra periodi diversi

    Returns:
        Dict con confronti mese corrente vs precedente e anno corrente vs precedente
    """
    if df is None or len(df) == 0:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])

    if category:
        df_copy = df_copy[df_copy['category'] == category]

    current_month = pd.Period.now('M')
    previous_month = current_month - 1

    current_year = pd.Period.now('Y')
    previous_year = current_year - 1

    # Spese mese corrente
    current_month_spending = df_copy[
        df_copy['date'].dt.to_period('M') == current_month
    ]['amount'].sum()

    # Spese mese precedente
    previous_month_spending = df_copy[
        df_copy['date'].dt.to_period('M') == previous_month
    ]['amount'].sum()

    # Spese anno corrente
    current_year_spending = df_copy[
        df_copy['date'].dt.to_period('Y') == current_year
    ]['amount'].sum()

    # Spese anno precedente
    previous_year_spending = df_copy[
        df_copy['date'].dt.to_period('Y') == previous_year
    ]['amount'].sum()

    # Calcola variazioni
    month_change = current_month_spending - previous_month_spending
    month_change_pct = (month_change / previous_month_spending * 100) if previous_month_spending > 0 else 0

    year_change = current_year_spending - previous_year_spending
    year_change_pct = (year_change / previous_year_spending * 100) if previous_year_spending > 0 else 0

    return {
        'current_month': current_month_spending,
        'previous_month': previous_month_spending,
        'month_change': month_change,
        'month_change_pct': month_change_pct,
        'current_year': current_year_spending,
        'previous_year': previous_year_spending,
        'year_change': year_change,
        'year_change_pct': year_change_pct
    }


def display_period_comparison(comparison):
    """Visualizza confronto tra periodi"""
    if comparison is None:
        return

    st.subheader("📅 Confronto Periodi")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Questo Mese",
            f"€{comparison['current_month']:,.2f}",
            delta=f"€{comparison['month_change']:,.2f} ({comparison['month_change_pct']:+.1f}%)",
            delta_color="inverse"
        )
        st.caption(f"Mese scorso: €{comparison['previous_month']:,.2f}")

    with col2:
        st.metric(
            "Quest'Anno",
            f"€{comparison['current_year']:,.2f}",
            delta=f"€{comparison['year_change']:,.2f} ({comparison['year_change_pct']:+.1f}%)",
            delta_color="inverse"
        )
        st.caption(f"Anno scorso: €{comparison['previous_year']:,.2f}")
