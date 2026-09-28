"""
Rowenta.it Scraper - Estrae ferri da stiro dal sito ufficiale Rowenta Italia
"""

import logging
from typing import List, Dict, Optional
from base_scraper import BaseScraper
import re
from urllib.parse import urljoin

logger = logging.getLogger('RowentaScraper')


class RowentaScraper(BaseScraper):
    """
    Scraper per Rowenta.it (sito ufficiale)
    URL base: https://www.rowenta.it/
    Ricerca ferri da stiro
    """

    def __init__(self, config: Dict):
        super().__init__('Rowenta.it', config)
        self.base_url = "https://www.rowenta.it"
        self.search_url = "https://www.rowenta.it/it/prodotti/ferri"

    def scrape_product_list(self, page: int = 1) -> List[Dict]:
        """
        Scrapa lista di ferri dal sito Rowenta.
        
        Args:
            page: Numero pagina (se supportato)
            
        Returns:
            Lista di prodotti
        """
        url = self.search_url if page == 1 else f"{self.search_url}?page={page}"
        
        soup = self._fetch_page(url)
        if not soup:
            return []

        products = []
        
        # Rowenta usa div.product-item o simile
        product_items = soup.find_all('div', {'class': re.compile(r'product.*item')})
        
        if not product_items:
            # Prova selettore alternativo
            product_items = soup.find_all('article', {'class': re.compile(r'product')})
        
        if not product_items:
            self.logger.warning(f"No products found on Rowenta page {page}")
            return []

        for idx, item in enumerate(product_items):
            try:
                # Link al prodotto
                link_elem = item.find('a', {'class': re.compile(r'product.*link')})
                if not link_elem or not link_elem.get('href'):
                    continue
                
                product_url = urljoin(self.base_url, link_elem['href'])

                # Nome prodotto
                name_elem = item.find('h2', {'class': 'product-name'})
                if not name_elem:
                    name_elem = item.find('a', {'class': re.compile(r'product.*name')})
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"

                # Prezzo
                price_elem = item.find('span', {'class': re.compile(r'price')})
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                price = self._extract_price(price_text)

                # Rating (se disponibile)
                rating_elem = item.find('span', {'class': re.compile(r'rating|stars')})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = self._extract_rating(rating_text)

                product = {
                    'source': 'Rowenta.it',
                    'name': name,
                    'price_eur': price,
                    'rating': rating,
                    'review_count': None,
                    'url': product_url,
                    'scrape_date': str(__import__('datetime').datetime.now())
                }
                
                products.append(product)
                self.logger.debug(f"Scraped product {idx + 1}: {name} - €{price}")

            except Exception as e:
                self.logger.error(f"Error scraping product: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(products)} products from Rowenta page {page}")
        return products

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa dettagli tecnici completi di un ferro Rowenta.
        Rowenta ha specifiche tecniche ben strutturate.
        
        Args:
            product_url: URL prodotto
            
        Returns:
            Dict con specifiche tecniche
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return {}

        details = {
            'url': product_url,
            'source': 'Rowenta.it',
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None,
            'title': self._extract_text(soup, 'h1.product-title', ''),
        }

        # Sezione specifiche tecniche
        # Rowenta spesso usa una tabella specs
        specs_table = soup.find('table', {'class': re.compile(r'spec')})
        
        if specs_table:
            rows = specs_table.find_all('tr')
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        # Parsing specifiche
                        if 'peso' in key:
                            details['kg'] = self._normalize_spec(value)
                        elif 'serbatoio' in key or 'capacità' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                details['serbatoio_ml'] = int(match.group(1))
                        elif 'cavo' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                details['cavo_cm'] = int(match.group(1))
                        elif 'vapore' in key or 'regolazione' in key:
                            details['vapore_setting'] = value
                        elif 'potenza' in key or 'watt' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                details['potenza_w'] = int(match.group(1))
                        elif 'colore' in key:
                            details['design_color'] = value
                        elif 'materiale' in key:
                            details['design_material'] = value

                except Exception as e:
                    self.logger.debug(f"Error parsing spec row: {str(e)}")
                    continue

        # Prova anche sezione caratteristiche in divs
        if not specs_table:
            features_div = soup.find('div', {'class': re.compile(r'features|specifications')})
            if features_div:
                for li in features_div.find_all('li'):
                    text = li.get_text(strip=True).lower()
                    if 'kg' in text:
                        match = re.search(r'(\d+[.,]\d+|\d+)\s*kg', text)
                        if match:
                            details['kg'] = float(match.group(1).replace(',', '.'))
                    if 'ml' in text:
                        match = re.search(r'(\d+)\s*ml', text)
                        if match:
                            details['serbatoio_ml'] = int(match.group(1))
                    if 'cm' in text and 'cavo' in text:
                        match = re.search(r'(\d+)\s*cm', text)
                        if match:
                            details['cavo_cm'] = int(match.group(1))
                    if 'w' in text:
                        match = re.search(r'(\d+)\s*w', text)
                        if match:
                            details['potenza_w'] = int(match.group(1))

        self.logger.info(f"Scraped details for {details.get('title', 'Unknown')}")
        return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 50) -> List[Dict]:
        """
        Rowenta non ha sempre reviews sul sito ufficiale.
        Questo metodo tenta di scrapare se presenti.
        
        Args:
            product_url: URL prodotto
            max_reviews: Max numero review
            
        Returns:
            Lista di review (vuota se non presenti)
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return []

        reviews = []

        # Cerca sezione reviews
        review_section = soup.find('section', {'class': re.compile(r'review|opinioni|valutazione')})
        
        if not review_section:
            self.logger.info("No reviews section found on Rowenta official product page")
            return reviews

        review_elements = review_section.find_all('div', {'class': re.compile(r'review.*item')})

        for review_elem in review_elements[:max_reviews]:
            try:
                # Titolo
                title_elem = review_elem.find(['h4', 'h3'])
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Rating
                rating_elem = review_elem.find('span', {'class': re.compile(r'rating|stars')})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = self._extract_rating(rating_text)

                # Testo
                text_elem = review_elem.find('p', {'class': re.compile(r'text|body')})
                text = text_elem.get_text(strip=True) if text_elem else ""

                # Autore
                author_elem = review_elem.find(['span', 'a'], {'class': re.compile(r'author|user')})
                author = author_elem.get_text(strip=True) if author_elem else "Anonymous"

                # Data
                date_elem = review_elem.find('span', {'class': re.compile(r'date')})
                date_str = date_elem.get_text(strip=True) if date_elem else ""

                review = {
                    'source': 'Rowenta.it',
                    'author': author,
                    'rating': rating,
                    'title': title,
                    'text': text,
                    'date_posted': date_str,
                    'helpful_count': None,
                }

                reviews.append(review)

            except Exception as e:
                self.logger.error(f"Error scraping review: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(reviews)} reviews from Rowenta")
        return reviews
