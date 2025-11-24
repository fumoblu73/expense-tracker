"""
Formatters per visualizzazione numeri e date in formato italiano
"""


def format_currency_ita(amount):
    """
    Formatta importo in formato italiano: punto migliaia, virgola decimali

    Args:
        amount: numero da formattare

    Returns:
        stringa formattata (es. "€1.234,56")
    """
    if amount is None:
        return "€0,00"

    # Formatta con punto migliaia e virgola decimali
    # Usa formato US poi sostituisci separatori
    formatted = f"{amount:,.2f}"  # Output: "1,234.56"

    # Inverti separatori per formato italiano
    # 1. Rimuovi virgole temporaneamente (saranno punti)
    # 2. Sostituisci punto decimale con virgola
    # 3. Aggiungi punto come separatore migliaia

    # Split su punto decimale
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')  # Virgole diventano punti
    decimal_part = parts[1] if len(parts) > 1 else '00'

    return f"€{integer_part},{decimal_part}"


def format_number_ita(number, decimals=2):
    """
    Formatta numero in formato italiano

    Args:
        number: numero da formattare
        decimals: numero di decimali (default: 2)

    Returns:
        stringa formattata (es. "1.234,56")
    """
    if number is None:
        return "0,00"

    # Formatta con separatori US
    formatted = f"{number:,.{decimals}f}"

    # Split su punto decimale
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')  # Virgole diventano punti
    decimal_part = parts[1] if len(parts) > 1 else '0' * decimals

    if decimals > 0:
        return f"{integer_part},{decimal_part}"
    else:
        return integer_part


def parse_italian_number(value):
    """
    Parse numero da formato italiano a float

    Args:
        value: stringa in formato italiano (es. "1.234,56")

    Returns:
        float
    """
    if isinstance(value, (int, float)):
        return float(value)

    # Rimuovi simbolo euro e spazi
    value = str(value).replace('€', '').replace(' ', '').strip()

    # Se c'è virgola, è il decimale italiano
    if ',' in value:
        value = value.replace('.', '')  # Rimuovi punti migliaia
        value = value.replace(',', '.')  # Virgola diventa punto decimale

    return float(value)
