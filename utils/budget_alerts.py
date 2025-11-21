"""
Sistema di alert per il monitoraggio dei budget
"""

import pandas as pd
import streamlit as st


def check_budget_alerts(transactions_df, categories_df, month=None):
    """
    Controlla se qualche categoria sta per superare il budget

    Args:
        transactions_df: DataFrame delle transazioni
        categories_df: DataFrame delle categorie con budget
        month: Periodo specifico da controllare (opzionale)

    Returns:
        Lista di alert con informazioni sullo stato del budget
    """
    alerts = []

    if transactions_df is None or len(transactions_df) == 0:
        return alerts

    if categories_df is None or len(categories_df) == 0:
        return alerts

    # Converti date
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Filtra per mese corrente se non specificato
    if month is None:
        month = pd.Period.now('M')

    month_transactions = df[df['date'].dt.to_period('M') == month]

    # Calcola spesa per categoria
    spending_by_category = month_transactions.groupby('category')['amount'].sum()

    # Controlla ogni categoria con budget
    for _, cat in categories_df.iterrows():
        category_name = cat['name']
        budget = cat['budget']

        if budget > 0:  # Solo categorie con budget impostato
            spent = spending_by_category.get(category_name, 0)
            percentage = (spent / budget) * 100
            remaining = budget - spent

            # Determina severità
            if percentage >= 100:
                severity = 'exceeded'
                icon = '🚨'
                color = 'error'
            elif percentage >= 90:
                severity = 'critical'
                icon = '⚠️'
                color = 'error'
            elif percentage >= 75:
                severity = 'warning'
                icon = '⚡'
                color = 'warning'
            elif percentage >= 50:
                severity = 'info'
                icon = 'ℹ️'
                color = 'info'
            else:
                severity = 'ok'
                icon = '✅'
                color = 'success'

            alerts.append({
                'category': category_name,
                'spent': spent,
                'budget': budget,
                'remaining': remaining,
                'percentage': percentage,
                'severity': severity,
                'icon': icon,
                'color': color
            })

    # Ordina per percentuale (più critici prima)
    alerts.sort(key=lambda x: x['percentage'], reverse=True)

    return alerts


def display_alerts(alerts, show_all=False):
    """
    Visualizza alert in Streamlit

    Args:
        alerts: Lista di alert da check_budget_alerts
        show_all: Se True, mostra tutti gli alert, altrimenti solo quelli critici
    """
    if not alerts:
        st.info("ℹ️ Nessun budget impostato. Configura i budget nelle categorie!")
        return

    # Filtra alert da mostrare
    if not show_all:
        alerts_to_show = [a for a in alerts if a['severity'] in ['exceeded', 'critical', 'warning']]
    else:
        alerts_to_show = alerts

    if not alerts_to_show:
        st.success("✅ Tutti i budget sono sotto controllo!")
        return

    # Mostra alert critici
    critical_alerts = [a for a in alerts_to_show if a['severity'] in ['exceeded', 'critical']]
    if critical_alerts:
        st.error("### 🚨 Alert Critici")
        for alert in critical_alerts:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.write(f"**{alert['icon']} {alert['category']}**")

                with col2:
                    if alert['severity'] == 'exceeded':
                        st.write(f"Sforato di €{abs(alert['remaining']):,.2f}")
                    else:
                        st.write(f"Rimangono €{alert['remaining']:,.2f}")

                with col3:
                    st.write(f"{alert['percentage']:.1f}% usato")

                # Barra di progresso
                progress_color = get_progress_color(alert['percentage'])
                st.progress(min(alert['percentage'] / 100, 1.0))

                st.caption(f"Speso: €{alert['spent']:,.2f} / Budget: €{alert['budget']:,.2f}")
                st.divider()

    # Mostra warning
    warning_alerts = [a for a in alerts_to_show if a['severity'] == 'warning']
    if warning_alerts:
        st.warning("### ⚡ Attenzione")
        for alert in warning_alerts:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.write(f"**{alert['icon']} {alert['category']}**")

                with col2:
                    st.write(f"Rimangono €{alert['remaining']:,.2f}")

                with col3:
                    st.write(f"{alert['percentage']:.1f}% usato")

                st.progress(alert['percentage'] / 100)
                st.caption(f"Speso: €{alert['spent']:,.2f} / Budget: €{alert['budget']:,.2f}")
                st.divider()

    # Mostra tutti gli altri se richiesto
    if show_all:
        other_alerts = [a for a in alerts_to_show if a['severity'] in ['info', 'ok']]
        if other_alerts:
            st.info("### 📊 Stato Budget")
            for alert in other_alerts:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.write(f"**{alert['icon']} {alert['category']}**")

                    with col2:
                        st.write(f"Rimangono €{alert['remaining']:,.2f}")

                    with col3:
                        st.write(f"{alert['percentage']:.1f}% usato")

                    st.progress(alert['percentage'] / 100)
                    st.caption(f"Speso: €{alert['spent']:,.2f} / Budget: €{alert['budget']:,.2f}")
                    st.divider()


def get_progress_color(percentage):
    """Restituisce il colore per la barra di progresso basato sulla percentuale"""
    if percentage >= 100:
        return '#FF0000'  # Rosso
    elif percentage >= 90:
        return '#FF4B4B'  # Rosso chiaro
    elif percentage >= 75:
        return '#FFA500'  # Arancione
    elif percentage >= 50:
        return '#FFD700'  # Giallo
    else:
        return '#4ECDC4'  # Verde acqua


def create_budget_summary_card(alerts):
    """Crea una card riassuntiva dello stato budget"""
    if not alerts:
        return None

    total_budget = sum(a['budget'] for a in alerts)
    total_spent = sum(a['spent'] for a in alerts)
    total_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0

    exceeded_count = len([a for a in alerts if a['severity'] == 'exceeded'])
    critical_count = len([a for a in alerts if a['severity'] == 'critical'])
    warning_count = len([a for a in alerts if a['severity'] == 'warning'])

    return {
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_percentage': total_percentage,
        'exceeded_count': exceeded_count,
        'critical_count': critical_count,
        'warning_count': warning_count
    }


def display_budget_summary(summary):
    """Visualizza card riassuntiva budget"""
    if summary is None:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Budget Totale",
            f"€{summary['total_budget']:,.2f}",
            delta=None
        )

    with col2:
        st.metric(
            "Speso",
            f"€{summary['total_spent']:,.2f}",
            delta=f"-€{summary['total_budget'] - summary['total_spent']:,.2f}"
        )

    with col3:
        percentage_emoji = "🔴" if summary['total_percentage'] >= 90 else "🟡" if summary['total_percentage'] >= 75 else "🟢"
        st.metric(
            "Utilizzo",
            f"{summary['total_percentage']:.1f}%",
            delta=None
        )
        st.write(percentage_emoji)

    with col4:
        issues = summary['exceeded_count'] + summary['critical_count'] + summary['warning_count']
        st.metric(
            "Alert",
            issues,
            delta=None
        )


def get_budget_recommendations(alerts):
    """Genera raccomandazioni basate sullo stato dei budget"""
    recommendations = []

    exceeded = [a for a in alerts if a['severity'] == 'exceeded']
    critical = [a for a in alerts if a['severity'] == 'critical']

    if exceeded:
        for alert in exceeded:
            recommendations.append({
                'type': 'critical',
                'message': f"Hai superato il budget per '{alert['category']}' di €{abs(alert['remaining']):,.2f}. Considera di ridurre le spese in questa categoria."
            })

    if critical:
        for alert in critical:
            recommendations.append({
                'type': 'warning',
                'message': f"Sei vicino al limite per '{alert['category']}'. Hai ancora €{alert['remaining']:,.2f} disponibili questo mese."
            })

    # Suggerimenti generali
    high_spending = [a for a in alerts if a['spent'] > 0]
    if high_spending:
        high_spending.sort(key=lambda x: x['spent'], reverse=True)
        top_category = high_spending[0]
        recommendations.append({
            'type': 'info',
            'message': f"La categoria con più spese è '{top_category['category']}' (€{top_category['spent']:,.2f}). Verifica se ci sono possibilità di risparmio."
        })

    return recommendations


def display_recommendations(recommendations):
    """Visualizza raccomandazioni"""
    if not recommendations:
        return

    st.subheader("💡 Suggerimenti")

    for rec in recommendations:
        if rec['type'] == 'critical':
            st.error(rec['message'])
        elif rec['type'] == 'warning':
            st.warning(rec['message'])
        else:
            st.info(rec['message'])
