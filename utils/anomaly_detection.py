"""
Rilevamento anomalie nelle spese
Identifica transazioni insolite basandosi su analisi statistica
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def detect_anomalies(transactions, lookback_months=3, threshold_std=2.0):
    """
    Rileva anomalie nelle transazioni basandosi su deviazione standard

    Args:
        transactions: DataFrame transazioni
        lookback_months: Mesi da considerare per calcolo statistiche (default: 3)
        threshold_std: Soglia in termini di deviazioni standard (default: 2.0)

    Returns:
        DataFrame con transazioni anomale e spiegazione
    """
    if len(transactions) == 0:
        return pd.DataFrame()

    # Converti date
    transactions = transactions.copy()
    transactions['date'] = pd.to_datetime(transactions['date'])

    # Filtra ultimi N mesi
    cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
    recent_trans = transactions[transactions['date'] >= cutoff_date]

    if len(recent_trans) == 0:
        return pd.DataFrame()

    anomalies = []

    # Analisi per categoria
    for category in recent_trans['category'].unique():
        if category in ['Entrate', 'Non Categorizzato']:
            continue

        cat_trans = recent_trans[recent_trans['category'] == category]

        if len(cat_trans) < 3:  # Serve almeno 3 transazioni per statistiche significative
            continue

        # Calcola statistiche
        mean_amount = cat_trans['amount'].mean()
        std_amount = cat_trans['amount'].std()

        if pd.isna(std_amount) or std_amount == 0:
            continue

        # Trova transazioni anomale (oltre threshold deviazioni standard)
        threshold = mean_amount + (threshold_std * std_amount)

        anomalous_trans = cat_trans[cat_trans['amount'] > threshold]

        for idx, trans in anomalous_trans.iterrows():
            # Calcola quanto è sopra la media
            deviation_pct = ((trans['amount'] - mean_amount) / mean_amount) * 100

            anomalies.append({
                'id': trans.get('id', idx),
                'date': trans['date'],
                'description': trans['description'],
                'amount': trans['amount'],
                'category': trans['category'],
                'mean_amount': mean_amount,
                'std_deviation': std_amount,
                'deviation_pct': deviation_pct,
                'explanation': f"{deviation_pct:.0f}% sopra la media per {category}",
                'severity': 'high' if deviation_pct > 200 else 'medium'
            })

    # Converti in DataFrame e ordina per severità
    if anomalies:
        df_anomalies = pd.DataFrame(anomalies)
        df_anomalies = df_anomalies.sort_values(['severity', 'deviation_pct'], ascending=[False, False])
        return df_anomalies

    return pd.DataFrame()


def detect_frequency_anomalies(transactions, lookback_months=3):
    """
    Rileva anomalie basate su frequenza insolita

    Identifica transazioni per merchant che compaiono più spesso del solito
    """
    if len(transactions) == 0 or 'description' not in transactions.columns:
        return pd.DataFrame()

    transactions = transactions.copy()
    transactions['date'] = pd.to_datetime(transactions['date'])

    # Analizza ultimi N mesi
    cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
    recent_trans = transactions[transactions['date'] >= cutoff_date]

    if len(recent_trans) < 10:  # Serve dataset minimo
        return pd.DataFrame()

    # Conta transazioni per merchant/descrizione
    trans_counts = recent_trans.groupby('description').size()

    # Media e deviazione standard delle frequenze
    mean_freq = trans_counts.mean()
    std_freq = trans_counts.std()

    if pd.isna(std_freq) or std_freq == 0:
        return pd.DataFrame()

    # Trova merchant con frequenza anomala (troppo alta)
    threshold = mean_freq + (2 * std_freq)
    high_freq_merchants = trans_counts[trans_counts > threshold]

    anomalies = []
    for merchant, count in high_freq_merchants.items():
        merchant_trans = recent_trans[recent_trans['description'] == merchant]
        total_amount = merchant_trans['amount'].sum()

        anomalies.append({
            'merchant': merchant,
            'transaction_count': count,
            'total_amount': total_amount,
            'avg_frequency': count / lookback_months,
            'explanation': f"Frequenza insolita: {count} transazioni in {lookback_months} mesi",
            'severity': 'medium'
        })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def detect_time_anomalies(transactions):
    """
    Rileva anomalie temporali (spese in orari/giorni insoliti)

    Nota: Richiede timestamp precisi che potrebbero non essere disponibili
    in tutti i formati bancari
    """
    # Placeholder per future implementazioni con orari precisi
    return pd.DataFrame()


def get_anomaly_summary(transactions, lookback_months=3):
    """
    Ottiene riepilogo completo delle anomalie

    Returns:
        dict con conteggi e dettagli anomalie
    """
    amount_anomalies = detect_anomalies(transactions, lookback_months)
    freq_anomalies = detect_frequency_anomalies(transactions, lookback_months)

    return {
        'amount_anomalies': amount_anomalies,
        'frequency_anomalies': freq_anomalies,
        'total_count': len(amount_anomalies) + len(freq_anomalies),
        'high_severity_count': len(amount_anomalies[amount_anomalies['severity'] == 'high']) if len(amount_anomalies) > 0 else 0,
        'medium_severity_count': len(amount_anomalies[amount_anomalies['severity'] == 'medium']) if len(amount_anomalies) > 0 else 0
    }
