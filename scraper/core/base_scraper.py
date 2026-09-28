"""
Base Scraper Class - Classe base per tutti gli scraper
Fornisce funzionalità comuni di parsing, error handling e logging
"""

import logging
import time
import random
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper(ABC):
    """
    Classe base per tutti gli scraper di ferri da stiro.
    Fornisce metodi comuni e interfaccia standardizzata.
    """

    def __init__(self, source_name: str, config: Dict):
        self.source_name = source_name
        self.config = config
        self.logger = logging.getLogger(self.source_name)
        self.session = self._create_session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]

    def _create_session(self) -> requests.Session:
        """Crea una sessione requests con header standard."""
        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session

    def _get_random_user_agent(self) -> str:
        """Ritorna un user-agent casuale."""
        return random.choice(self.user_agents)

    def _fetch_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch una pagina HTML con retry logic.
        
        Args:
            url: URL da scrapare
            max_retries: Numero massimo di tentativi
            
        Returns:
            BeautifulSoup object o None se fallisce
        """
        for attempt in range(max_retries):
            try:
                # Delay per evitare rate limiting
                delay = self.config.get('delay_between_requests', 2)
                time.sleep(delay + random.uniform(0, 2))

                # Fetch con user-agent randomico
                headers = {'User-Agent': self._get_random_user_agent()}
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.config.get('timeout_seconds', 30)
                )
                response.raise_for_status()

                self.logger.debug(f"Fetched {url} successfully")
                return BeautifulSoup(response.content, 'html.parser')

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue

        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def _extract_text(self, soup: BeautifulSoup, selector: str, default: str = "N/A") -> str:
        """
        Estrae testo da un elemento HTML.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            default: Valore di default se non trovato
            
        Returns:
            Testo estratto o default
        """
        try:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                return text if text else default
        except Exception as e:
            self.logger.debug(f"Error extracting text with selector '{selector}': {str(e)}")
        return default

    def _extract_price(self, price_text: str) -> Optional[float]:
        """
        Estrae prezzo numerico da testo.
        
        Args:
            price_text: Testo contenente il prezzo (es. "€ 79,99")
            
        Returns:
            Prezzo come float o None
        """
        try:
            # Rimuovi simboli di valuta e spazi
            cleaned = price_text.replace('€', '').replace('$', '').replace(',', '.').strip()
            # Prendi solo il primo numero
            import re
            match = re.search(r'\d+\.?\d*', cleaned)
            if match:
                return float(match.group())
        except Exception as e:
            self.logger.debug(f"Error extracting price from '{price_text}': {str(e)}")
        return None

    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """
        Estrae rating numerico da testo.
        
        Args:
            rating_text: Testo contenente il rating (es. "4,5 su 5")
            
        Returns:
            Rating come float o None
        """
        try:
            import re
            match = re.search(r'\d+[.,]\d+', rating_text)
            if match:
                rating_str = match.group().replace(',', '.')
                return float(rating_str)
        except Exception as e:
            self.logger.debug(f"Error extracting rating from '{rating_text}': {str(e)}")
        return None

    def _normalize_spec(self, value: str, unit: str = "") -> Optional[float]:
        """
        Normalizza valori numerici da specifiche.
        
        Args:
            value: Valore con possibili unità
            unit: Unità attesa
            
        Returns:
            Valore numerico o None
        """
        try:
            import re
            # Estrai numero
            match = re.search(r'\d+[.,]\d+|\d+', value)
            if match:
                num_str = match.group().replace(',', '.')
                return float(num_str)
        except Exception as e:
            self.logger.debug(f"Error normalizing spec '{value}': {str(e)}")
        return None

    @abstractmethod
    def scrape_product_list(self) -> List[Dict]:
        """
        Scrapa la lista di prodotti dalla pagina di ricerca.
        Deve essere implementato da subclass.
        
        Returns:
            Lista di dict con info prodotto (name, price, url, rating, etc.)
        """
        pass

    @abstractmethod
    def scrape_product_details(self, product_url: str) -> Dict:
        """
        Scrapa i dettagli di un singolo prodotto.
        Deve essere implementato da subclass.
        
        Args:
            product_url: URL del prodotto
            
        Returns:
            Dict con dettagli completi (specs, reviews, etc.)
        """
        pass

    @abstractmethod
    def scrape_reviews(self, product_url: str, max_reviews: int = 50) -> List[Dict]:
        """
        Scrapa le review di un prodotto.
        Deve essere implementato da subclass.
        
        Args:
            product_url: URL del prodotto
            max_reviews: Numero massimo di review da scrapare
            
        Returns:
            Lista di dict con dati review
        """
        pass
