"""
Formatters per visualizzazione numeri e date in formato italiano
"""


def format_currency_ita(amount):
    """
    Formatta importo in formato italiano: punto migliaia, virgola decimali

    Args:
        amount: numero da formattare

    Returns:
        stringa formattata (es. "€1.234,56" o "€80,00")
    """
    if amount is None:
        return "€0,00"

    # Formatta con 2 decimali
    formatted = f"{amount:.2f}"  # Output: "80.00" o "1234.56"

    # Separa parte intera e decimali
    if '.' in formatted:
        integer_str, decimal_str = formatted.split('.')
    else:
        integer_str = formatted
        decimal_str = "00"

    # Aggiungi punti ogni 3 cifre per la parte intera (da destra a sinistra)
    # Es: "1234567" -> "1.234.567"
    integer_with_dots = ""
    for i, digit in enumerate(reversed(integer_str)):
        if i > 0 and i % 3 == 0:
            integer_with_dots = "." + integer_with_dots
        integer_with_dots = digit + integer_with_dots

    return f"€{integer_with_dots},{decimal_str}"


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
