"""
Main Scraper Orchestrator - Coordina tutti gli scraper per l'analisi competitiva
"""

import logging
import json
from typing import List, Dict
from datetime import datetime
import sys
import os

# Importa tutti gli scraper
from amazon_scraper_playwright import AmazonPlaywrightScraper
from opinioni_scraper import OpinioniScraper
from rowenta_scraper import RowentaScraper
from retailer_scrapers import MediaworldScraper, LidlScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MainOrchestrator')


class ScraperOrchestrator:
    """
    Orchestrator principale che gestisce tutti gli scraper.
    Coordina l'estrazione dei dati da tutte le fonti.
    """

    def __init__(self, config_path: str = 'config_ferro_da_stiro.json'):
        """
        Inizializza l'orchestrator.
        
        Args:
            config_path: Path al file di configurazione
        """
        self.config = self._load_config(config_path)
        self.scrapers = self._initialize_scrapers()
        self.all_products = []
        self.all_reviews = []

    def _load_config(self, config_path: str) -> Dict:
        """Carica file di configurazione."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Configurazione di default."""
        return {
            'delay_between_requests': 2,
            'timeout_seconds': 30,
            'max_retries': 3,
        }

    def _initialize_scrapers(self) -> Dict:
        """Inizializza tutti gli scraper."""
        scrapers = {}
        
        if self.config.get('sources', {}).get('amazon_it', {}).get('enabled', True):
            scrapers['amazon'] = AmazonPlaywrightScraper(self.config)
        
        if self.config.get('sources', {}).get('opinioni_it', {}).get('enabled', True):
            scrapers['opinioni'] = OpinioniScraper(self.config)
        
        if self.config.get('sources', {}).get('rowenta_it', {}).get('enabled', True):
            scrapers['rowenta'] = RowentaScraper(self.config)
        
        if self.config.get('sources', {}).get('mediaworld_it', {}).get('enabled', True):
            scrapers['mediaworld'] = MediaworldScraper(self.config)
        
        if self.config.get('sources', {}).get('lidl_it', {}).get('enabled', True):
            scrapers['lidl'] = LidlScraper(self.config)
        
        logger.info(f"Initialized {len(scrapers)} scrapers: {list(scrapers.keys())}")
        return scrapers

    def scrape_all_product_lists(self, max_pages: int = 1) -> List[Dict]:
        """
        Scrapa lista prodotti da tutte le fonti.
        
        Args:
            max_pages: Numero massimo di pagine per fonte
            
        Returns:
            Lista complessiva di prodotti
        """
        logger.info(f"Starting to scrape product lists from {len(self.scrapers)} sources...")
        
        for source_name, scraper in self.scrapers.items():
            logger.info(f"Scraping {source_name}...")
            try:
                for page in range(1, max_pages + 1):
                    products = scraper.scrape_product_list(page)
                    self.all_products.extend(products)
                    
                    if not products:  # Se pagina vuota, ferma la paginazione
                        break
                        
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
                continue
        
        logger.info(f"Total products scraped: {len(self.all_products)}")
        return self.all_products

    def scrape_product_details(self, product_limit: int = 10) -> None:
        """
        Scrapa dettagli per ogni prodotto.
        
        Args:
            product_limit: Limite di prodotti per cui scrapare dettagli
        """
        logger.info(f"Scraping details for {min(product_limit, len(self.all_products))} products...")
        
        for product in self.all_products[:product_limit]:
            try:
                source = product['source'].lower().replace('.it', '')
                scraper = self.scrapers.get(source)
                
                if not scraper:
                    logger.warning(f"No scraper found for source: {product['source']}")
                    continue
                
                product_url = product.get('url', '')
                if not product_url:
                    logger.warning(f"Product has empty URL, skipping: {product.get('name', 'Unknown')}")
                    continue
                
                details = scraper.scrape_product_details(product_url)
                product.update(details)
                
            except Exception as e:
                logger.error(f"Error scraping details for {product.get('name', 'Unknown')}: {str(e)}")
                continue

    def scrape_reviews(self, product_limit: int = 5, reviews_per_product: int = 20) -> None:
        """
        Scrapa review per prodotti selezionati.
        
        Args:
            product_limit: Numero di prodotti per cui scrapare review
            reviews_per_product: Numero massimo di review per prodotto
        """
        logger.info(f"Scraping reviews for {min(product_limit, len(self.all_products))} products...")
        
        for product in self.all_products[:product_limit]:
            try:
                source = product['source'].lower().replace('.it', '')
                scraper = self.scrapers.get(source)
                
                if not scraper:
                    continue
                
                product_url = product.get('url', '')
                if not product_url:
                    continue
                
                reviews = scraper.scrape_reviews(
                    product_url,
                    max_reviews=reviews_per_product
                )
                
                # Associa prodotto alle review
                for review in reviews:
                    review['product_id'] = product.get('name', '')
                    review['product_url'] = product['url']
                
                self.all_reviews.extend(reviews)
                
            except Exception as e:
                logger.error(f"Error scraping reviews for {product.get('name', 'Unknown')}: {str(e)}")
                continue

    def export_products_json(self, output_file: str = 'products.json') -> None:
        """Esporta prodotti in JSON."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_products, f, ensure_ascii=False, indent=2)
            logger.info(f"Exported {len(self.all_products)} products to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting products: {str(e)}")

    def export_reviews_json(self, output_file: str = 'reviews.json') -> None:
        """Esporta review in JSON."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_reviews, f, ensure_ascii=False, indent=2)
            logger.info(f"Exported {len(self.all_reviews)} reviews to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting reviews: {str(e)}")

    def export_products_csv(self, output_file: str = 'products.csv') -> None:
        """Esporta prodotti in CSV."""
        try:
            import csv
            if not self.all_products:
                logger.warning("No products to export")
                return
            
            # Prendi tutte le chiavi
            fieldnames = set()
            for product in self.all_products:
                fieldnames.update(product.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.all_products)
            
            logger.info(f"Exported {len(self.all_products)} products to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")

    def get_statistics(self) -> Dict:
        """Ritorna statistiche dei dati scrapati."""
        stats = {
            'total_products': len(self.all_products),
            'total_reviews': len(self.all_reviews),
            'products_per_source': {},
            'avg_rating': None,
            'price_range': {},
            'avg_rating_by_source': {}
        }

        # Prodotti per source
        for product in self.all_products:
            source = product.get('source', 'Unknown')
            stats['products_per_source'][source] = stats['products_per_source'].get(source, 0) + 1

        # Statistiche prezzo
        prices = [p.get('price_eur') for p in self.all_products if p.get('price_eur')]
        if prices:
            stats['price_range'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices)
            }

        # Statistiche rating
        ratings = [p.get('rating') for p in self.all_products if p.get('rating')]
        if ratings:
            stats['avg_rating'] = sum(ratings) / len(ratings)
            
            # Rating per source
            for product in self.all_products:
                if product.get('rating'):
                    source = product.get('source', 'Unknown')
                    if source not in stats['avg_rating_by_source']:
                        stats['avg_rating_by_source'][source] = []
                    stats['avg_rating_by_source'][source].append(product['rating'])
            
            # Calcola media per source
            for source, ratings_list in stats['avg_rating_by_source'].items():
                stats['avg_rating_by_source'][source] = sum(ratings_list) / len(ratings_list)

        return stats

    def print_report(self) -> None:
        """Stampa un report riassuntivo."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("SCRAPING REPORT - Ferro da Stiro")
        print("="*60)
        print(f"Total products: {stats['total_products']}")
        print(f"Total reviews: {stats['total_reviews']}")
        
        print("\nProducts per source:")
        for source, count in stats['products_per_source'].items():
            print(f"  {source}: {count}")
        
        if stats['price_range']:
            print(f"\nPrice range: €{stats['price_range']['min']:.2f} - €{stats['price_range']['max']:.2f}")
            print(f"Average price: €{stats['price_range']['avg']:.2f}")
        
        if stats['avg_rating']:
            print(f"\nAverage rating: {stats['avg_rating']:.2f}")
            print("Average rating by source:")
            for source, rating in stats['avg_rating_by_source'].items():
                print(f"  {source}: {rating:.2f}")
        
        print("="*60 + "\n")

    def close_all_scrapers(self) -> None:
        """Chiude tutti gli scraper (utile per Selenium)."""
        for scraper_name, scraper in self.scrapers.items():
            try:
                if hasattr(scraper, 'close'):
                    scraper.close()
                    logger.info(f"Closed scraper: {scraper_name}")
            except Exception as e:
                logger.warning(f"Error closing {scraper_name}: {str(e)}")

    def run_full_scrape(self, max_pages: int = 1, product_details_limit: int = 10, reviews_limit: int = 5):
        """
        Esegue uno scraping completo.
        
        Args:
            max_pages: Pagine da scrapare per source
            product_details_limit: Numero di prodotti per cui scrapare dettagli
            reviews_limit: Numero di prodotti per cui scrapare review
        """
        logger.info("Starting full scrape...")
        
        try:
            # 1. Scrapa lista prodotti
            self.scrape_all_product_lists(max_pages=max_pages)
            
            # 2. Scrapa dettagli
            self.scrape_product_details(product_limit=product_details_limit)
            
            # 3. Scrapa review
            self.scrape_reviews(product_limit=reviews_limit)
            
            # 4. Esporta dati
            self.export_products_json('products.json')
            self.export_products_csv('products.csv')
            self.export_reviews_json('reviews.json')
            
            # 5. Stampa report
            self.print_report()
            
            logger.info("Full scrape completed!")
            
        finally:
            # 6. Chiudi tutti gli scraper (Selenium, etc.)
            self.close_all_scrapers()


if __name__ == '__main__':
    # Esegui scraping
    orchestrator = ScraperOrchestrator()
    
    # Per test veloce: 1 pagina, 5 prodotti con details, 3 con reviews
    orchestrator.run_full_scrape(
        max_pages=1,
        product_details_limit=5,
        reviews_limit=3
    )