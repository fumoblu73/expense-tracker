"""
Utilità per gestione spese ricorrenti e calcoli budget disponibile
"""

import pandas as pd
from datetime import datetime
from calendar import monthrange


def calculate_available_balance(transactions, categories, recurring_expenses, year=None, month=None):
    """
    Calcola il budget disponibile per il resto del mese

    Args:
        transactions: DataFrame transazioni
        categories: DataFrame categorie con budget
        recurring_expenses: DataFrame spese ricorrenti attive
        year: Anno (default: corrente)
        month: Mese (default: corrente)

    Returns:
        dict con dettagli calcolo
    """
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    # 1. Budget totale mensile
    total_budget = categories['budget'].sum()

    # 2. Speso fino ad oggi
    if len(transactions) > 0:
        transactions['date'] = pd.to_datetime(transactions['date'])
        current_month_trans = transactions[
            (transactions['date'].dt.year == year) &
            (transactions['date'].dt.month == month)
        ]
        spent_so_far = current_month_trans['amount'].sum()
    else:
        spent_so_far = 0

    # 3. Spese ricorrenti ancora da pagare questo mese
    recurring_pending = 0

    if len(recurring_expenses) > 0:
        recurring_monthly = 0

        for _, rec in recurring_expenses.iterrows():
            if not rec['active']:
                continue

            if rec['frequency'] == 'mensile':
                recurring_monthly += rec['amount']
            elif rec['frequency'] == 'annuale':
                # Converti annuale in mensile
                if pd.to_datetime(rec['start_date']).month == month:
                    recurring_monthly += rec['amount']
                else:
                    recurring_monthly += rec['amount'] / 12

        recurring_pending = recurring_monthly

    # 4. Calcola disponibile
    available = total_budget - spent_so_far - recurring_pending

    # 5. Giorni rimasti nel mese
    now = datetime.now()
    if year == now.year and month == now.month:
        days_in_month = monthrange(year, month)[1]
        days_remaining = days_in_month - now.day + 1
        daily_allowance = available / days_remaining if days_remaining > 0 else 0
    else:
        days_remaining = 0
        daily_allowance = 0

    # 6. Percentuale budget usato
    budget_usage_pct = (spent_so_far / total_budget * 100) if total_budget > 0 else 0

    return {
        'total_budget': total_budget,
        'spent': spent_so_far,
        'recurring_pending': recurring_pending,
        'available': available,
        'days_remaining': days_remaining,
        'daily_allowance': daily_allowance,
        'budget_usage_pct': budget_usage_pct,
        'is_negative': available < 0
    }


def get_recurring_status_for_month(transactions, recurring_expenses, year=None, month=None):
    """
    Verifica quali spese ricorrenti sono state pagate nel mese

    Returns:
        DataFrame con status (paid/pending) per ogni spesa ricorrente
    """
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    if len(recurring_expenses) == 0:
        return pd.DataFrame()

    status_list = []

    for _, rec in recurring_expenses.iterrows():
        if not rec['active']:
            continue

        # Cerca transazioni simili nel mese
        if len(transactions) > 0:
            transactions['date'] = pd.to_datetime(transactions['date'])
            month_trans = transactions[
                (transactions['date'].dt.year == year) &
                (transactions['date'].dt.month == month) &
                (transactions['category'] == rec['category'])
            ]

            # Controlla se c'è una transazione simile per importo
            similar_trans = month_trans[
                (month_trans['amount'] >= rec['amount'] * 0.9) &
                (month_trans['amount'] <= rec['amount'] * 1.1)
            ]

            is_paid = len(similar_trans) > 0
        else:
            is_paid = False

        status_list.append({
            'name': rec['name'],
            'category': rec['category'],
            'amount': rec['amount'],
            'frequency': rec['frequency'],
            'status': 'paid' if is_paid else 'pending'
        })

    return pd.DataFrame(status_list)
