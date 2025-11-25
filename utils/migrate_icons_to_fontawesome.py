"""
Script di migrazione per convertire le icone emoji in icone Font Awesome
Esegui questo script una sola volta per aggiornare il database esistente
"""

import sqlite3
from pathlib import Path

# Mapping emoji → Font Awesome
ICON_MIGRATION_MAP = {
    '🛒': 'fa-cart-shopping',
    '🚗': 'fa-car',
    '💡': 'fa-bolt',
    '🍽️': 'fa-utensils',
    '🛍️': 'fa-bag-shopping',
    '⚕️': 'fa-heart-pulse',
    '🎬': 'fa-film',
    '🏠': 'fa-house',
    '💰': 'fa-money-bill-wave',
    '📦': 'fa-box',
    '❓': 'fa-circle-question',
    '💳': 'fa-credit-card',
    '📱': 'fa-mobile-screen',
    '✈️': 'fa-plane',
    '⚡': 'fa-bolt',
    '🍕': 'fa-pizza-slice',
    '🎁': 'fa-gift',
    '💊': 'fa-pills',
    '🏃': 'fa-person-running',
    '📚': 'fa-book',
    '🐾': 'fa-paw',
}


def migrate_icons_to_fontawesome(db_path="data/expenses.db"):
    """
    Migra tutte le icone emoji a Font Awesome nel database

    Args:
        db_path: Percorso al database

    Returns:
        Numero di categorie aggiornate
    """
    if not Path(db_path).exists():
        print(f"❌ Database non trovato: {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Leggi tutte le categorie
    cursor.execute("SELECT name, icon FROM categories")
    categories = cursor.fetchall()

    updated_count = 0

    for name, icon in categories:
        # Controlla se è un'emoji che deve essere migrata
        if icon in ICON_MIGRATION_MAP:
            new_icon = ICON_MIGRATION_MAP[icon]

            # Aggiorna l'icona
            cursor.execute(
                "UPDATE categories SET icon = ? WHERE name = ?",
                (new_icon, name)
            )

            print(f"✅ Aggiornato: {name} | {icon} → {new_icon}")
            updated_count += 1
        elif icon.startswith('fa-'):
            print(f"⏭️  Già Font Awesome: {name} | {icon}")
        else:
            print(f"ℹ️  Emoji custom mantenuta: {name} | {icon}")

    conn.commit()
    conn.close()

    return updated_count


if __name__ == "__main__":
    print("🔄 Migrazione icone emoji → Font Awesome")
    print("=" * 50)

    updated = migrate_icons_to_fontawesome()

    print("=" * 50)
    print(f"✅ Migrazione completata: {updated} categorie aggiornate")
