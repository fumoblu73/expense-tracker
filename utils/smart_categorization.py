"""
Sistema di categorizzazione automatica intelligente
Estrae merchant dalle descrizioni e applica apprendimento automatico
"""

import re


def extract_merchant(description):
    """
    Estrae il nome del merchant dalla descrizione bancaria

    Args:
        description: Stringa descrizione dalla banca

    Returns:
        Nome merchant pulito o None
    """
    if not description or pd.isna(description):
        return None

    desc_lower = str(description).lower()

    # Pattern comuni nelle descrizioni bancarie italiane
    patterns = [
        # Formato: "pagamento con carta - carta *XXXX-MERCHANT città"
        r'carta\s*\*\d+-([^-\d]+?)(?:\s+[a-z]{2,}\s+[a-z]{2}\s+ita|\s+roma)',
        # Formato: "spesa pagobancomat - carta *XXXX-MERCHANT"
        r'carta\s*\*\d+-([^-]+?)(?:\s+via|\s+cc|\s+\d{5})',
        # Bonifici e pagamenti vari
        r'bonifico.*?da\s+([A-Z][A-Z\s]+?)(?:\s+via|\s+-|$)',
        # Generico: prendi il testo dopo ultimo "-"
        r'-\s*([a-zA-Z][a-zA-Z\s\.\']+?)(?:\s+\d|$)'
    ]

    for pattern in patterns:
        match = re.search(pattern, desc_lower, re.IGNORECASE)
        if match:
            merchant = match.group(1).strip()
            # Pulisci il merchant
            merchant = clean_merchant_name(merchant)
            if len(merchant) > 3:  # Nome valido
                return merchant

    # Fallback: cerca nomi comuni di negozi/servizi
    known_merchants = [
        'todis', 'conad', 'coop', 'esselunga', 'carrefour', 'lidl', 'md',
        'eni', 'q8', 'ip', 'esso', 'tamoil',
        'ovs', 'zara', 'h&m', 'decathlon', 'nike',
        'bar', 'ristorante', 'pizzeria', 'mcdonald',
        'farmacia', 'tabacchi',
        'inps', 'agenzia entrate', 'enel', 'tim', 'vodafone', 'wind'
    ]

    for merchant in known_merchants:
        if merchant in desc_lower:
            return merchant.capitalize()

    return None


def clean_merchant_name(merchant):
    """Pulisce il nome del merchant rimuovendo parti inutili"""
    merchant = merchant.strip()

    # Rimuovi parole comuni non significative
    remove_words = ['spa', 's.p.a.', 'srl', 's.r.l.', 'snc', 's.n.c.', 'sas', 's.a.s.']
    for word in remove_words:
        merchant = re.sub(r'\b' + word + r'\b', '', merchant, flags=re.IGNORECASE)

    # Rimuovi spazi multipli
    merchant = re.sub(r'\s+', ' ', merchant).strip()

    # Capitalizza prima lettera di ogni parola
    merchant = ' '.join(word.capitalize() for word in merchant.split())

    return merchant


def auto_categorize_by_keywords(description, amount_sign=None):
    """
    Categorizza automaticamente basandosi su parole chiave

    Args:
        description: Descrizione transazione
        amount_sign: 'income' o 'expense' per identificare tipo transazione

    Returns:
        Nome categoria suggerita
    """
    if not description:
        return 'Non Categorizzato'

    desc_lower = str(description).lower()

    # PRIMA: Se è un'entrata, categorizza con categorie entrate specifiche
    if amount_sign == 'income':
        return categorize_income(desc_lower)

    # Dizionario parole chiave -> categoria SPESE
    keywords = {
        'Alimentari': [
            'todis', 'conad', 'coop', 'esselunga', 'carrefour', 'lidl', 'eurospin',
            'pam', 'simply', 'aldi', 'md', 'penny', 'iper', 'supermercato',
            'gestra', 'ortofrutta', 'panificio', 'alimentari'
        ],
        'Trasporti': [
            'benzina', 'gasolio', 'diesel', 'eni', 'q8', 'ip', 'esso', 'agip',
            'tamoil', 'trenitalia', 'italo', 'atac', 'atm', 'autobus', 'metro',
            'taxi', 'uber', 'car sharing', 'parcheggio', 'ztl', 'autostradale'
        ],
        'Ristoranti': [
            'bar', 'ristorante', 'pizzeria', 'trattoria', 'osteria', 'pub',
            'mcdonald', 'burger king', 'kfc', 'rossopomodoro', 'old wild west',
            'caffe', 'caffè', 'gelateria', 'pasticceria', 'colibri'
        ],
        'Utenze': [
            'enel', 'eni gas', 'iren', 'acea', 'hera', 'a2a',
            'tim', 'vodafone', 'wind', 'tre', 'fastweb', 'telecom',
            'netflix', 'amazon prime', 'spotify', 'sky', 'dazn',
            'acqua', 'gas', 'luce', 'rifiuti', 'tari'
        ],
        'Shopping': [
            'ovs', 'zara', 'h&m', 'bershka', 'pull&bear', 'stradivarius',
            'decathlon', 'nike', 'adidas', 'foot locker',
            'amazon', 'ebay', 'zalando', 'yoox',
            'ikea', 'leroy merlin', 'brico', 'mediaworld', 'unieuro',
            'gamestop', 'fnac', 'feltrinelli'
        ],
        'Salute': [
            'farmacia', 'parafarmacia', 'dottore', 'medico', 'dentista',
            'ospedale', 'clinica', 'asl', 'laboratorio analisi',
            'ottico', 'fisioterapista'
        ],
        'Casa': [
            'affitto', 'condominio', 'idraulico', 'elettricista', 'imbianchino',
            'fabbro', 'falegname', 'giardiniere', 'pulizie'
        ],
        'Svago': [
            'cinema', 'teatro', 'concerto', 'museo', 'mostra',
            'palestra', 'piscina', 'sport', 'calcio', 'tennis',
            'spa', 'terme', 'massaggio', 'parrucchiere', 'barbiere',
            'estetista', 'centro estetico'
        ]
    }

    # Cerca corrispondenza
    for category, words in keywords.items():
        if any(word in desc_lower for word in words):
            return category

    return 'Non Categorizzato'


def categorize_income(description):
    """
    Categorizza specificamente le ENTRATE

    Args:
        description: Descrizione transazione (già lowercase)

    Returns:
        Categoria entrata specifica
    """
    # Categorie specifiche per ENTRATE
    income_keywords = {
        'Stipendio': [
            'stipendio', 'salario', 'busta paga', 'cedolino', 'retribuzione',
            'compenso', 'paga', 'salary'
        ],
        'Pensione': [
            'pensione', 'inps', 'inpdap', 'assegno pensione'
        ],
        'Bonifico': [
            'bonifico', 'bon.', 'accredito bonifico', 'trasferimento',
            'wire transfer', 'sepa'
        ],
        'Rimborso': [
            'rimborso', 'storno', 'reso', 'refund', 'restituzione',
            'indennizzo', 'risarcimento'
        ],
        'Sussidi': [
            'assegno unico', 'assegni familiari', 'bonus', 'reddito di cittadinanza',
            'cassa integrazione', 'disoccupazione', 'naspi', 'inps assegno'
        ],
        'Investimenti': [
            'dividendi', 'interessi', 'cedola', 'capital gain', 'plusvalenza',
            'rendita', 'coupon'
        ],
        'Altro Reddito': [
            'vendita', 'prestazione', 'consulenza', 'fattura', 'incasso'
        ]
    }

    # Cerca corrispondenza
    for category, words in income_keywords.items():
        if any(word in description for word in words):
            return category

    # Default per entrate non riconosciute
    return 'Altro Reddito'


import pandas as pd

def smart_categorize_transactions(df, db):
    """
    Categorizza intelligentemente tutte le transazioni
    Usa apprendimento precedente + categorizzazione automatica

    Args:
        df: DataFrame con transazioni
        db: Istanza ExpenseDB

    Returns:
        DataFrame con colonna 'category' aggiornata e 'merchant' estratto
    """
    merchants = []
    categories = []

    for idx, row in df.iterrows():
        description = row.get('description', '')
        amount = row.get('amount', 0)
        amount_sign = row.get('amount_sign', 'expense')

        # Estrai merchant
        merchant = extract_merchant(description)
        merchants.append(merchant)

        # Prova a recuperare categoria appresa (per SPESE)
        if amount_sign == 'expense' and merchant:
            learned_cat = db.get_learned_category(merchant)
            if learned_cat:
                categories.append(learned_cat)
                continue

        # Usa categorizzazione automatica (gestisce sia entrate che spese)
        auto_cat = auto_categorize_by_keywords(description, amount_sign)
        categories.append(auto_cat)

    df['merchant'] = merchants
    df['category'] = categories

    return df
