# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MarketProductIntelligence - Main Entry Point
Coordina il web scraping di ferri da stiro da multiple sorgenti
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Aggiungi scraper directory al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper', 'core'))

from main_scraper import ScraperOrchestrator


def setup_directories():
    """Crea le directory necessarie se non esistono."""
    directories = [
        'scraper/output',
        'scraper/logs',
        'data/raw',
        'data/processed',
        'reports'
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def main():
    """Main function - Entry point del progetto."""
    
    parser = argparse.ArgumentParser(
        description='MarketProductIntelligence - Web Scraping di Ferri da Stiro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:

  python main.py --quick
  python main.py --full
  python main.py --pages 3 --products 30 --reviews 15
        """
    )

    parser.add_argument('--quick', action='store_true', help='Esegui quick test')
    parser.add_argument('--full', action='store_true', help='Esegui scraping completo')
    parser.add_argument('--pages', type=int, default=1, help='Numero pagine (default: 1)')
    parser.add_argument('--products', type=int, default=10, help='Numero prodotti (default: 10)')
    parser.add_argument('--reviews', type=int, default=5, help='Numero prodotti reviews (default: 5)')
    parser.add_argument('--config', type=str, default='scraper/config/config_ferro_da_stiro.json', help='Path config')
    parser.add_argument('--source', type=str, choices=['amazon', 'opinioni', 'rowenta', 'mediaworld', 'lidl', 'all'], default='all', help='Scraper singola fonte')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Setup directories
    setup_directories()

    # Determina i parametri
    if args.full:
        pages = 2
        products = 20
        reviews = 10
        print("[MODALITA] SCRAPING COMPLETO")
    else:
        pages = args.pages
        products = args.products
        reviews = args.reviews
        print("[MODALITA] QUICK TEST")

    # Carica configurazione
    config_path = args.config
    if not os.path.exists(config_path):
        print("ERRORE: File di configurazione non trovato: " + config_path)
        sys.exit(1)

    print("\n[PARAMETRI]")
    print("  - Pagine per sorgente: " + str(pages))
    print("  - Prodotti con dettagli: " + str(products))
    print("  - Prodotti con reviews: " + str(reviews))
    print("  - Configurazione: " + config_path)

    # Inizializza orchestrator
    print("\n[INIT] Inizializzazione orchestrator...")
    try:
        orchestrator = ScraperOrchestrator(config_path)
    except Exception as e:
        print("ERRORE nell'inizializzazione: " + str(e))
        sys.exit(1)

    # Se sorgente specifica, disabilita le altre
    if args.source != 'all':
        scrapers_to_remove = [s for s in orchestrator.scrapers.keys() if s != args.source]
        for scraper_name in scrapers_to_remove:
            del orchestrator.scrapers[scraper_name]
        print("OK - Scrapata solo la sorgente: " + args.source)

    # Esegui scraping
    print("\n[START] Avvio scraping...\n")
    try:
        orchestrator.run_full_scrape(
            max_pages=pages,
            product_details_limit=products,
            reviews_limit=reviews
        )
        
        print("\nOK - Scraping completato con successo!")
        print("\n[OUTPUT] File generati:")
        print("  - products.json")
        print("  - products.csv")
        print("  - reviews.json")
        print("  - scraper.log")
        
    except KeyboardInterrupt:
        print("\nAVVISO - Scraping interrotto dall'utente")
        sys.exit(0)
    except Exception as e:
        print("\nERRORE durante lo scraping: " + str(e))
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
