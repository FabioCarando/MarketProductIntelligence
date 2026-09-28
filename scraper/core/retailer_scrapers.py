"""
Mediaworld.it e Lidl.it Scrapers - Estrattori di ferri da stiro da retailer
"""

import logging
from typing import List, Dict, Optional
from base_scraper import BaseScraper
import re
from urllib.parse import urljoin

logger = logging.getLogger('RetailerScrapers')


# ============================================================================
# MEDIAWORLD SCRAPER
# ============================================================================

class MediaworldScraper(BaseScraper):
    """
    Scraper per Mediaworld.it
    Retailer online con sezione elettrodomestici
    """

    def __init__(self, config: Dict):
        super().__init__('Mediaworld.it', config)
        self.base_url = "https://www.mediaworld.it"
        self.search_url = "https://www.mediaworld.it/categorie/casa-e-giardino/cucina-piccoli-elettrodomestici/ferri-da-stiro-3"

    def scrape_product_list(self, page: int = 1) -> List[Dict]:
        """
        Scrapa lista ferri da stiro da Mediaworld.
        
        Args:
            page: Numero pagina
            
        Returns:
            Lista prodotti
        """
        url = f"{self.search_url}?page={page}" if page > 1 else self.search_url
        
        soup = self._fetch_page(url)
        if not soup:
            return []

        products = []
        
        # Mediaworld usa una struttura con div.product o article.product-item
        product_items = soup.find_all(['div', 'article'], {'class': re.compile(r'product|item')})
        
        if not product_items:
            self.logger.warning(f"No products found on Mediaworld page {page}")
            return []

        for idx, item in enumerate(product_items):
            try:
                # Link prodotto
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                
                product_url = urljoin(self.base_url, link_elem['href'])

                # Nome
                name_elem = item.find(['h2', 'h3', 'span'], {'class': re.compile(r'name|title')})
                name = name_elem.get_text(strip=True) if name_elem else link_elem.get_text(strip=True)

                # Prezzo
                price_elem = item.find('span', {'class': re.compile(r'price|cost')})
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                price = self._extract_price(price_text)

                # Rating
                rating_elem = item.find('span', {'class': re.compile(r'rating|stars')})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = self._extract_rating(rating_text)

                product = {
                    'source': 'Mediaworld.it',
                    'name': name,
                    'price_eur': price,
                    'rating': rating,
                    'review_count': None,
                    'url': product_url,
                    'scrape_date': str(__import__('datetime').datetime.now())
                }
                
                products.append(product)
                self.logger.debug(f"Scraped: {name} - €{price}")

            except Exception as e:
                self.logger.error(f"Error scraping product: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(products)} products from Mediaworld page {page}")
        return products

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa dettagli prodotto Mediaworld.
        
        Args:
            product_url: URL prodotto
            
        Returns:
            Dict con specifiche
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return {}

        details = {
            'url': product_url,
            'source': 'Mediaworld.it',
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None,
            'title': self._extract_text(soup, ['h1', '.product-name'], ''),
        }

        # Sezione specifiche tecniche
        specs_section = soup.find('section', {'class': re.compile(r'spec|characteristic|feature')})
        
        if specs_section:
            for row in specs_section.find_all(['div', 'tr'], {'class': re.compile(r'spec|row')}):
                try:
                    label = row.find(['span', 'td'], {'class': re.compile(r'label|name')})
                    value = row.find(['span', 'td'], {'class': re.compile(r'value')})
                    
                    if label and value:
                        key = label.get_text(strip=True).lower()
                        val_text = value.get_text(strip=True)

                        if 'peso' in key:
                            details['kg'] = self._normalize_spec(val_text)
                        elif 'serbatoio' in key:
                            match = re.search(r'(\d+)', val_text)
                            if match:
                                details['serbatoio_ml'] = int(match.group(1))
                        elif 'cavo' in key:
                            match = re.search(r'(\d+)', val_text)
                            if match:
                                details['cavo_cm'] = int(match.group(1))
                        elif 'vapore' in key:
                            details['vapore_setting'] = val_text
                        elif 'potenza' in key:
                            match = re.search(r'(\d+)', val_text)
                            if match:
                                details['potenza_w'] = int(match.group(1))
                        elif 'colore' in key:
                            details['design_color'] = val_text

                except Exception as e:
                    self.logger.debug(f"Error parsing spec: {str(e)}")
                    continue

        self.logger.info(f"Scraped details for {details.get('title', 'Unknown')}")
        return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 50) -> List[Dict]:
        """Mediaworld non sempre ha reviews nella pagina."""
        return []  # Per ora non implementato


# ============================================================================
# LIDL SCRAPER
# ============================================================================

class LidlScraper(BaseScraper):
    """
    Scraper per Lidl.it
    Supermercato online con sezione elettrodomestici
    """

    def __init__(self, config: Dict):
        super().__init__('Lidl.it', config)
        self.base_url = "https://www.lidl.it"
        self.search_url = "https://www.lidl.it/c/casa-e-cucina/elettrodomestici"

    def scrape_product_list(self, page: int = 1) -> List[Dict]:
        """
        Scrapa ferri da stiro da Lidl.it
        
        Args:
            page: Numero pagina
            
        Returns:
            Lista prodotti
        """
        url = f"{self.search_url}?page={page}" if page > 1 else self.search_url
        
        soup = self._fetch_page(url)
        if not soup:
            return []

        products = []
        
        # Lidl usa struttura con div.product-tile o simile
        product_items = soup.find_all(['div', 'article'], {'class': re.compile(r'product|tile')})
        
        if not product_items:
            self.logger.warning(f"No products found on Lidl page {page}")
            return []

        for idx, item in enumerate(product_items):
            try:
                # Link
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                
                product_url = urljoin(self.base_url, link_elem['href'])

                # Nome
                name_elem = item.find(['h2', 'h3', 'span'], {'class': re.compile(r'name|title')})
                name = name_elem.get_text(strip=True) if name_elem else link_elem.get_text(strip=True)

                # Prezzo
                price_elem = item.find('span', {'class': re.compile(r'price|cost')})
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                price = self._extract_price(price_text)

                # Lidl solitamente non ha rating nella ricerca
                rating = None

                product = {
                    'source': 'Lidl.it',
                    'name': name,
                    'price_eur': price,
                    'rating': rating,
                    'review_count': None,
                    'url': product_url,
                    'scrape_date': str(__import__('datetime').datetime.now())
                }
                
                products.append(product)
                self.logger.debug(f"Scraped: {name} - €{price}")

            except Exception as e:
                self.logger.error(f"Error scraping product: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(products)} products from Lidl page {page}")
        return products

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa dettagli prodotto Lidl.
        
        Args:
            product_url: URL prodotto
            
        Returns:
            Dict con specifiche
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return {}

        details = {
            'url': product_url,
            'source': 'Lidl.it',
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None,
            'title': self._extract_text(soup, ['h1', '.product-name'], ''),
        }

        # Sezione caratteristiche
        features_section = soup.find('section', {'class': re.compile(r'feature|spec|detail')})
        
        if features_section:
            for item in features_section.find_all(['li', 'div', 'tr']):
                try:
                    text = item.get_text(strip=True).lower()
                    
                    if 'kg' in text:
                        match = re.search(r'(\d+[.,]\d+|\d+)\s*kg', text)
                        if match:
                            details['kg'] = float(match.group(1).replace(',', '.'))
                    if 'ml' in text or 'capacità' in text:
                        match = re.search(r'(\d+)\s*ml', text)
                        if match:
                            details['serbatoio_ml'] = int(match.group(1))
                    if 'cm' in text and 'cavo' in text:
                        match = re.search(r'(\d+)\s*cm', text)
                        if match:
                            details['cavo_cm'] = int(match.group(1))
                    if 'w' in text or 'watt' in text:
                        match = re.search(r'(\d+)\s*w', text)
                        if match:
                            details['potenza_w'] = int(match.group(1))

                except Exception as e:
                    self.logger.debug(f"Error parsing feature: {str(e)}")
                    continue

        self.logger.info(f"Scraped details for {details.get('title', 'Unknown')}")
        return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 50) -> List[Dict]:
        """Lidl non ha reviews sulla pagina prodotto."""
        return []  # Non implementato
