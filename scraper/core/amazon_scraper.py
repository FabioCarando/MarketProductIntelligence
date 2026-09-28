"""
Amazon.it Scraper - Estrae ferri da stiro da Amazon Italia
Utilizza BeautifulSoup per parsing HTML statico
"""

import logging
from typing import List, Dict, Optional
from base_scraper import BaseScraper
import re
from urllib.parse import urljoin

logger = logging.getLogger('AmazonScraper')


class AmazonScraper(BaseScraper):
    """
    Scraper per Amazon.it
    URL base ricerca: https://www.amazon.it/s?k=ferro+da+stiro
    """

    def __init__(self, config: Dict):
        super().__init__('Amazon.it', config)
        self.base_url = "https://www.amazon.it"
        self.search_url = "https://www.amazon.it/s?k=ferro+da+stiro"

    def scrape_product_list(self, page: int = 1) -> List[Dict]:
        """
        Scrapa lista di ferri da stiro dalla pagina di ricerca Amazon.
        
        Args:
            page: Numero pagina
            
        Returns:
            Lista di prodotti con name, price, rating, url
        """
        # URL con paginazione (Amazon usa parametri di query)
        url = f"{self.search_url}&page={page}"
        
        soup = self._fetch_page(url)
        if not soup:
            return []

        products = []
        
        # Selettore per ogni item di prodotto nella griglia
        # Amazon usa div.s-result-item per ogni prodotto
        product_items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        if not product_items:
            self.logger.warning(f"No products found on Amazon page {page}")
            return []

        for idx, item in enumerate(product_items):
            try:
                # Link al prodotto
                link_elem = item.find('a', {'class': 's-no-outline'})
                if not link_elem or not link_elem.get('href'):
                    continue
                
                product_url = urljoin(self.base_url, link_elem['href'])

                # Nome prodotto (h2 span dentro il link)
                name_elem = item.find('h2', {'class': 's-size-mini'})
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"

                # Prezzo (span con classe price)
                price_elem = item.find('span', {'class': 'a-price-whole'})
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                price = self._extract_price(price_text)

                # Rating (span con icona stella)
                rating_elem = item.find('span', {'class': 'a-icon-star-small'})
                rating_text = rating_elem.get_text(strip=True) if rating_elem else ""
                rating = self._extract_rating(rating_text)

                # Numero reviews
                review_count = 0
                review_elem = item.find('span', {'aria-label': re.compile(r'voto.*su 5')})
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    match = re.search(r'(\d+)', review_text)
                    if match:
                        review_count = int(match.group(1))

                product = {
                    'source': 'Amazon.it',
                    'name': name,
                    'price_eur': price,
                    'rating': rating,
                    'review_count': review_count,
                    'url': product_url,
                    'scrape_date': str(__import__('datetime').datetime.now())
                }
                
                products.append(product)
                self.logger.debug(f"Scraped product {idx + 1}: {name} - €{price}")

            except Exception as e:
                self.logger.error(f"Error scraping product item: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(products)} products from Amazon page {page}")
        return products

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa i dettagli completi di un prodotto Amazon.
        Estrae: specs, dimensioni, potenza, peso, capacità serbatoio, lunghezza cavo
        
        Args:
            product_url: URL prodotto Amazon
            
        Returns:
            Dict con details completi
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return {}

        details = {
            'url': product_url,
            'source': 'Amazon.it',
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None,
            'title': self._extract_text(soup, 'h1#title', ''),
        }

        # Tabella specifiche (Amazon usa una tabella HTML)
        # Cerchiamo le specifiche nella tabella
        specs_table = soup.find('table', {'class': 'a-keyvalue'})
        
        if specs_table:
            rows = specs_table.find_all('tr')
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        # Mapping delle specifiche
                        if 'peso' in key:
                            details['kg'] = self._normalize_spec(value)
                        elif 'serbatoio' in key or 'capacità' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                details['serbatoio_ml'] = int(match.group(1))
                        elif 'cavo' in key or 'lunghezza del cavo' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                details['cavo_cm'] = int(match.group(1))
                        elif 'vapore' in key or 'regolazione del vapore' in key:
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

        # Se non trovia la tabella, prova sezioni featurebullets
        if not specs_table:
            bullets = soup.find('ul', {'class': 'a-unordered-list'})
            if bullets:
                for li in bullets.find_all('li'):
                    text = li.get_text(strip=True).lower()
                    # Prova a estrarre specifiche dal testo
                    if 'kg' in text:
                        match = re.search(r'(\d+[.,]\d+|\d+)\s*kg', text)
                        if match:
                            details['kg'] = float(match.group(1).replace(',', '.'))
                    if 'ml' in text or 'ml' in text:
                        match = re.search(r'(\d+)\s*ml', text)
                        if match:
                            details['serbatoio_ml'] = int(match.group(1))
                    if 'cm' in text and 'cavo' in text:
                        match = re.search(r'(\d+)\s*cm', text)
                        if match:
                            details['cavo_cm'] = int(match.group(1))

        self.logger.info(f"Scraped details for {details.get('title', 'Unknown')}")
        return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 50) -> List[Dict]:
        """
        Scrapa le review di un prodotto Amazon.
        
        Args:
            product_url: URL prodotto
            max_reviews: Max numero review da scrapare
            
        Returns:
            Lista di review dict
        """
        # Modifica URL per accedere alla pagina reviews
        reviews_url = product_url.split('?')[0] + '#customerReviews'
        
        soup = self._fetch_page(reviews_url)
        if not soup:
            return []

        reviews = []

        # Amazon carica reviews dinamicamente con JavaScript
        # Questo scraper statico troverà le review visibili nella pagina
        review_elements = soup.find_all('div', {'data-hook': 'review'})

        for review_elem in review_elements[:max_reviews]:
            try:
                # Rating
                rating_elem = review_elem.find('i', {'data-icon-type': 'star'})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.find('span', {'class': 'a-icon-star'})
                    if rating_text:
                        rating = self._extract_rating(rating_text.get_text(strip=True))

                # Titolo review
                title_elem = review_elem.find('a', {'data-hook': 'review-title'})
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Testo review
                body_elem = review_elem.find('span', {'data-hook': 'review-body'})
                text = body_elem.get_text(strip=True) if body_elem else ""

                # Autore
                author_elem = review_elem.find('a', {'class': 'a-profile-name'})
                author = author_elem.get_text(strip=True) if author_elem else "Anonymous"

                # Data
                date_elem = review_elem.find('span', {'data-hook': 'review-date'})
                date_str = date_elem.get_text(strip=True) if date_elem else ""

                # Numero di persone che trovano la review utile
                helpful_elem = review_elem.find('span', {'data-hook': 'helpful-vote-statement'})
                helpful_count = 0
                if helpful_elem:
                    helpful_text = helpful_elem.get_text(strip=True)
                    match = re.search(r'(\d+)', helpful_text)
                    if match:
                        helpful_count = int(match.group(1))

                review = {
                    'source': 'Amazon.it',
                    'author': author,
                    'rating': rating,
                    'title': title,
                    'text': text,
                    'date_posted': date_str,
                    'helpful_count': helpful_count,
                }

                reviews.append(review)

            except Exception as e:
                self.logger.error(f"Error scraping review: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(reviews)} reviews")
        return reviews
