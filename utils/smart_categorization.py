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


def auto_categorize_by_keywords(description, amount_sign=None, db=None):
    """
    Categorizza automaticamente basandosi su parole chiave

    Args:
        description: Descrizione transazione
        amount_sign: 'income' o 'expense' per identificare tipo transazione
        db: Database manager (opzionale, per apprendimento entrate)

    Returns:
        Nome categoria suggerita
    """
    if not description:
        return 'Non Categorizzato'

    desc_lower = str(description).lower()

    # PRIORITÀ MASSIMA: Prelievi bancomat identificati per numero carta
    # *1282 = Emanuele, *4951 = Cinzia
    if 'prel' in desc_lower:
        if '1282' in desc_lower:
            return 'Prelievo Emanuele'
        elif '4951' in desc_lower:
            return 'Prelievo Cinzia'

    # PRIMA: Se è un'entrata, categorizza con categorie entrate specifiche
    if amount_sign == 'income':
        return categorize_income(desc_lower, db=db)

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


def categorize_income(description, db=None):
    """
    Categorizza specificamente le ENTRATE con sistema di apprendimento

    Args:
        description: Descrizione transazione (già lowercase)
        db: Database manager (opzionale, per apprendimento)

    Returns:
        Categoria entrata specifica
    """
    # PRIORITA' 1: Pattern appresi dall'utente (se db disponibile)
    if db:
        learned_category = db.get_learned_income_category(description)
        if learned_category:
            return learned_category

    # PRIORITA' 2: Keyword matching con ordine specifico -> generico
    # Categorie specifiche per ENTRATE (ordinate per specificità)
    income_keywords = {
        # SPECIFICHE PRIMA (multi-parola, più precise)
        'Sussidi': [
            'assegno unico', 'assegni familiari', 'inps assegno',
            'cassa integrazione', 'disoccupazione', 'naspi',
            'bonus', 'reddito di cittadinanza'
        ],
        'Pensione': [
            'pensione inps', 'pensione inpdap', 'assegno pensione',
            'inpdap'  # Rimosso 'inps' generico
        ],
        'Stipendio': [
            'busta paga', 'stipendio', 'salario', 'cedolino',
            'retribuzione', 'compenso', 'paga', 'salary'
        ],
        'Investimenti': [
            'dividendi', 'interessi', 'cedola', 'capital gain',
            'plusvalenza', 'rendita', 'coupon'
        ],
        # GENERICHE DOPO (singole parole, meno precise)
        'Rimborso': [
            'rimborso', 'storno', 'reso', 'refund',
            'restituzione', 'indennizzo', 'risarcimento'
        ],
        'Bonifico': [
            'bonifico', 'bon.', 'accredito bonifico', 'trasferimento',
            'wire transfer', 'sepa'
        ],
        'Altro Reddito': [
            'vendita', 'prestazione', 'consulenza', 'fattura', 'incasso'
        ]
    }

    # Cerca corrispondenza (ordine del dizionario mantiene priorità Python 3.7+)
    for category, words in income_keywords.items():
        if any(word in description for word in words):
            return category

    # Default per entrate non riconosciute
    return 'Altro Reddito'


import pandas as pd

def smart_categorize_transactions(df, db):
    """
    Categorizza intelligentemente tutte le transazioni.
    Usa apprendimento precedente + categorizzazione automatica.

    Ottimizzazione bulk: carica merchant e income patterns in 2 query totali
    invece di 1 query per riga (evita N+1 problem su dataset grandi).
    """
    # ── Carica tutto il DB in memoria con 2 query ──────────────────────────
    merchant_map = {}  # {merchant_lower: category}
    try:
        all_merchants = db.get_all_learned_merchants()
        if len(all_merchants) > 0:
            for _, row in all_merchants.iterrows():
                merchant_map[str(row['merchant']).lower()] = row['category']
    except Exception:
        pass

    income_patterns = []  # [(pattern, category)] ordinati per lunghezza desc
    try:
        all_income = db.get_all_learned_income_patterns()
        if len(all_income) > 0:
            income_patterns = sorted(
                [(str(r['description_pattern']), r['category']) for _, r in all_income.iterrows()],
                key=lambda x: len(x[0]),
                reverse=True
            )
    except Exception:
        pass

    # ── Categorizzazione in-memory (zero query di rete per riga) ───────────
    merchants = []
    categories = []

    for _, row in df.iterrows():
        description = row.get('description', '')
        amount_sign = row.get('amount_sign', 'expense')

        merchant = extract_merchant(description)
        merchants.append(merchant)

        # Spese: cerca merchant nel dict in-memory
        if amount_sign == 'expense' and merchant:
            learned_cat = merchant_map.get(merchant.lower())
            if learned_cat:
                categories.append(learned_cat)
                continue

        # Entrate: cerca income pattern in-memory
        if amount_sign == 'income' and income_patterns:
            desc_lower = str(description).lower()
            # Normalizza (rimuovi variabili) come fa db.normalize_income_description
            try:
                normalized = db.normalize_income_description(desc_lower)
            except Exception:
                normalized = desc_lower
            # Match esatto
            exact = next((cat for pat, cat in income_patterns if pat == normalized), None)
            if exact:
                categories.append(exact)
                continue
            # Match parziale: pattern più lungo i cui termini sono tutti presenti
            partial = next(
                (cat for pat, cat in income_patterns if all(w in normalized for w in pat.split())),
                None
            )
            if partial:
                categories.append(partial)
                continue

        # Fallback: keyword matching (100% in-memory, nessuna query DB)
        auto_cat = auto_categorize_by_keywords(description, amount_sign, db=None)
        categories.append(auto_cat)

    df['merchant'] = merchants
    df['category'] = categories

    return df
