"""
Opinioni.it Scraper - Estrae ferri da stiro e reviews da Opinioni.it
Portale italiano con review su prodotti
"""

import logging
from typing import List, Dict, Optional
from base_scraper import BaseScraper
import re
from urllib.parse import urljoin

logger = logging.getLogger('OpinioniScraper')


class OpinioniScraper(BaseScraper):
    """
    Scraper per Opinioni.it
    URL base ricerca: https://www.opinioni.it/ricerca/ferro%20da%20stiro
    """

    def __init__(self, config: Dict):
        super().__init__('Opinioni.it', config)
        self.base_url = "https://www.opinioni.it"
        self.search_url = "https://www.opinioni.it/ricerca/ferro%20da%20stiro"

    def scrape_product_list(self, page: int = 1) -> List[Dict]:
        """
        Scrapa lista di ferri da stiro dal portale di review Opinioni.it
        
        Args:
            page: Numero pagina
            
        Returns:
            Lista di prodotti con info base
        """
        # URL con paginazione
        url = f"{self.search_url}?pag={page}"
        
        soup = self._fetch_page(url)
        if not soup:
            return []

        products = []
        
        # Opinioni.it usa una struttura con div.productContainer
        product_containers = soup.find_all('div', {'class': 'productContainer'})
        
        if not product_containers:
            # Prova selettore alternativo
            product_containers = soup.find_all('div', {'class': 'p-list-item'})
        
        if not product_containers:
            self.logger.warning(f"No products found on Opinioni.it page {page}")
            return []

        for idx, container in enumerate(product_containers):
            try:
                # Link al prodotto
                link_elem = container.find('a', {'class': 'productName'})
                if not link_elem or not link_elem.get('href'):
                    continue
                
                product_url = urljoin(self.base_url, link_elem['href'])

                # Nome prodotto
                name = link_elem.get_text(strip=True)

                # Rating medio
                rating_elem = container.find('span', {'class': 'rateValue'})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = self._extract_rating(rating_text)

                # Numero opinioni/reviews
                opinions_elem = container.find('span', {'class': 'opinionsNum'})
                review_count = 0
                if opinions_elem:
                    opinions_text = opinions_elem.get_text(strip=True)
                    match = re.search(r'(\d+)', opinions_text)
                    if match:
                        review_count = int(match.group(1))

                # Categoria/Marca (spesso non disponibile nella lista)
                brand = "Unknown"
                brand_elem = container.find('span', {'class': 'brand'})
                if brand_elem:
                    brand = brand_elem.get_text(strip=True)

                product = {
                    'source': 'Opinioni.it',
                    'name': name,
                    'brand': brand,
                    'price_eur': None,  # Opinioni.it non mostra prezzi nella lista
                    'rating': rating,
                    'review_count': review_count,
                    'url': product_url,
                    'scrape_date': str(__import__('datetime').datetime.now())
                }
                
                products.append(product)
                self.logger.debug(f"Scraped product {idx + 1}: {name} - Rating: {rating}")

            except Exception as e:
                self.logger.error(f"Error scraping product: {str(e)}")
                continue

        self.logger.info(f"Scraped {len(products)} products from Opinioni.it page {page}")
        return products

    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa i dettagli di un prodotto da Opinioni.it.
        Opinioni.it è un portale di reviews, non sempre ha specifiche tecniche complete.
        
        Args:
            product_url: URL prodotto
            
        Returns:
            Dict con dettagli disponibili
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return {}

        details = {
            'url': product_url,
            'source': 'Opinioni.it',
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None,
            'title': self._extract_text(soup, 'h1.productTitle', ''),
            'rating_avg': None,
            'review_count': None,
        }

        # Sezione rating/votes
        rating_elem = soup.find('span', {'class': 'productRating'})
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            details['rating_avg'] = self._extract_rating(rating_text)

        # Numero di opinioni
        opinions_elem = soup.find('span', {'class': 'numOpinions'})
        if opinions_elem:
            opinions_text = opinions_elem.get_text(strip=True)
            match = re.search(r'(\d+)', opinions_text)
            if match:
                details['review_count'] = int(match.group(1))

        # Sezione specifiche tecniche (se presente)
        specs_section = soup.find('div', {'class': 'specifications'})
        if specs_section:
            spec_items = specs_section.find_all('div', {'class': 'spec-item'})
            for spec_item in spec_items:
                try:
                    label = spec_item.find('span', {'class': 'spec-label'})
                    value = spec_item.find('span', {'class': 'spec-value'})
                    
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
        """
        Scrapa le opinioni/review di un prodotto da Opinioni.it.
        Opinioni.it è specializzato in review di prodotti.
        
        Args:
            product_url: URL prodotto
            max_reviews: Max numero review
            
        Returns:
            Lista di review dict
        """
        soup = self._fetch_page(product_url)
        if not soup:
            return []

        reviews = []

        # Opinioni.it ha div.opinion per ogni review
        opinion_elements = soup.find_all('div', {'class': 'opinion'})

        if not opinion_elements:
            # Prova selettore alternativo
            opinion_elements = soup.find_all('div', {'class': 'review-item'})

        for opinion_elem in opinion_elements[:max_reviews]:
            try:
                # Titolo opinione
                title_elem = opinion_elem.find('h3', {'class': 'opinionTitle'})
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Testo opinione
                text_elem = opinion_elem.find('div', {'class': 'opinionText'})
                text = text_elem.get_text(strip=True) if text_elem else ""

                # Valutazione (stelle)
                rating_elem = opinion_elem.find('span', {'class': 'stars'})
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = self._extract_rating(rating_text)

                # Autore
                author_elem = opinion_elem.find('span', {'class': 'authorName'})
                author = author_elem.get_text(strip=True) if author_elem else "Anonymous"

                # Data
                date_elem = opinion_elem.find('span', {'class': 'opinionDate'})
                date_str = date_elem.get_text(strip=True) if date_elem else ""

                # Utilità dell'opinione
                useful_elem = opinion_elem.find('span', {'class': 'usefulVotes'})
                helpful_count = 0
                if useful_elem:
                    useful_text = useful_elem.get_text(strip=True)
                    match = re.search(r'(\d+)', useful_text)
                    if match:
                        helpful_count = int(match.group(1))

                review = {
                    'source': 'Opinioni.it',
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

        self.logger.info(f"Scraped {len(reviews)} reviews from Opinioni.it")
        return reviews
