# -*- coding: utf-8 -*-
"""
Amazon.it Scraper using Selenium for dynamic content
Handles JavaScript-rendered pages and extracts product details and reviews
"""

import time
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from base_scraper import BaseScraper


class AmazonSeleniumScraper(BaseScraper):
    """Scraper for Amazon.it using Selenium for dynamic content"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Amazon scraper with Selenium"""
        # Initialize attributes first
        self.driver = None
        self.wait = None
        self.source_name = "Amazon.it"
        self.base_url = "https://www.amazon.it/s?k=ferro+da+stiro"
        
        # Call parent __init__ with BOTH source_name and config
        super().__init__(self.source_name, config)
        
        # Initialize the driver after parent init
        self._init_driver()

    def _init_driver(self):
        """Initialize Chrome WebDriver with headless mode"""
        try:
            import os
            import stat
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Get ChromeDriver path
            driver_path = ChromeDriverManager().install()
            
            # Fix permissions on Windows (if needed)
            if os.name == 'nt':  # Windows
                try:
                    os.chmod(driver_path, stat.S_IRWXU)  # Give execute permission
                    logging.info(f"[Amazon Selenium] Set execute permission on {driver_path}")
                except Exception as perm_error:
                    logging.warning(f"[Amazon Selenium] Could not set permissions: {str(perm_error)}")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logging.info("[Amazon Selenium] Driver initialized successfully")
        except Exception as e:
            logging.error(f"[Amazon Selenium] Failed to initialize driver: {str(e)}")
            raise

    def fetch_products(self, max_pages: int = 1, product_details_limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch product listings from Amazon.it using Selenium"""
        products = []
        product_count = 0

        try:
            for page in range(1, max_pages + 1):
                if product_count >= product_details_limit:
                    break

                url = f"{self.base_url}&page={page}"
                logging.info(f"[Amazon Selenium] Fetching page {page}: {url}")
                
                self.driver.get(url)
                time.sleep(3)  # Wait for JS rendering

                # Wait for product container to load
                try:
                    self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                        )
                    )
                except:
                    logging.warning(f"[Amazon Selenium] Page {page} took too long to load")

                # Extract product elements
                product_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-component-type='s-search-result']"
                )

                logging.info(f"[Amazon Selenium] Found {len(product_elements)} products on page {page}")

                for product_elem in product_elements:
                    if product_count >= product_details_limit:
                        break

                    try:
                        product_data = self._parse_product_element(product_elem)
                        if product_data:
                            products.append(product_data)
                            product_count += 1
                            logging.info(f"[Amazon Selenium] Extracted product {product_count}: {product_data.get('name', 'Unknown')}")
                    except Exception as e:
                        logging.warning(f"[Amazon Selenium] Error parsing product: {str(e)}")
                        continue

        except Exception as e:
            logging.error(f"[Amazon Selenium] Error in fetch_products: {str(e)}")
        
        logging.info(f"[Amazon Selenium] Fetched total {len(products)} products")
        return products

    def _parse_product_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse individual product element from Selenium"""
        try:
            # Product name
            name_elem = element.find_element(By.CSS_SELECTOR, "h2 span")
            name = name_elem.text.strip() if name_elem else "Unknown"

            # Product URL
            link_elem = element.find_element(By.CSS_SELECTOR, "h2 a")
            url = link_elem.get_attribute("href") if link_elem else ""

            # Price
            price_text = ""
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                price_text = price_elem.text.strip()
            except:
                pass

            price = self._extract_price(price_text)

            # Rating
            rating = None
            try:
                rating_elem = element.find_element(By.CSS_SELECTOR, "span.a-icon-star-small span")
                rating_text = rating_elem.text.split()[0]
                rating = float(rating_text)
            except:
                pass

            # Review count
            review_count = 0
            try:
                review_elem = element.find_element(By.CSS_SELECTOR, "span[aria-label*='valutazioni']")
                review_text = review_elem.text.strip()
                review_count = int(re.sub(r'\D', '', review_text.split()[0]))
            except:
                pass

            product = {
                'name': name,
                'url': url,
                'price_eur': price,
                'rating': rating,
                'review_count': review_count,
                'source': self.source_name,
                'scrape_date': datetime.now().isoformat(),
                'kg': None,
                'serbatoio_ml': None,
                'cavo_cm': None,
                'vapore_setting': None,
                'potenza_w': None,
                'design_color': None,
                'design_material': None
            }

            # Try to extract specs from product title
            product.update(self._extract_specs_from_title(name))

            return product

        except Exception as e:
            logging.error(f"[Amazon Selenium] Error parsing product element: {str(e)}")
            return None

    def _extract_specs_from_title(self, title: str) -> Dict[str, Any]:
        """Extract specifications from product title using regex"""
        specs = {}

        # Power (Watt)
        power_match = re.search(r'(\d{3,4})\s*W(?:att)?', title, re.IGNORECASE)
        if power_match:
            specs['potenza_w'] = int(power_match.group(1))

        # Weight (kg)
        kg_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*kg', title, re.IGNORECASE)
        if kg_match:
            specs['kg'] = float(kg_match.group(1).replace(',', '.'))

        # Tank/Serbatoio (ml)
        tank_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(?:ml|cc)', title, re.IGNORECASE)
        if tank_match:
            specs['serbatoio_ml'] = float(tank_match.group(1).replace(',', '.'))

        # Cord length (cm)
        cord_match = re.search(r'cavo\s+(\d+)\s*cm', title, re.IGNORECASE)
        if cord_match:
            specs['cavo_cm'] = int(cord_match.group(1))

        # Steam settings
        steam_match = re.search(r'(\d+)\s*impostazioni?\s+vapore', title, re.IGNORECASE)
        if steam_match:
            specs['vapore_setting'] = int(steam_match.group(1))

        return specs

    def fetch_reviews(self, product_url: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch reviews for a specific product using Selenium"""
        reviews = []

        if not product_url:
            return reviews

        try:
            logging.info(f"[Amazon Selenium] Fetching reviews for: {product_url}")
            
            # Navigate to product page
            self.driver.get(product_url)
            time.sleep(2)

            # Scroll to reviews section
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Find and click "See more reviews" if available
            try:
                see_reviews_btn = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']")
                    )
                )
                see_reviews_btn.click()
                time.sleep(3)
            except:
                pass

            # Extract review elements
            review_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-hook='review']"
            )

            logging.info(f"[Amazon Selenium] Found {len(review_elements)} reviews")

            for review_elem in review_elements[:limit]:
                try:
                    review_data = self._parse_review_element(review_elem, product_url)
                    if review_data:
                        reviews.append(review_data)
                except Exception as e:
                    logging.warning(f"[Amazon Selenium] Error parsing review: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"[Amazon Selenium] Error fetching reviews: {str(e)}")

        return reviews

    def _parse_review_element(self, element, product_url: str) -> Optional[Dict[str, Any]]:
        """Parse individual review element"""
        try:
            # Author
            author = "Anonymous"
            try:
                author_elem = element.find_element(By.CSS_SELECTOR, ".a-profile-name")
                author = author_elem.text.strip()
            except:
                pass

            # Rating
            rating = None
            try:
                rating_elem = element.find_element(By.CSS_SELECTOR, "span[data-hook='review-star-rating'] span")
                rating_text = rating_elem.text.split()[0]
                rating = float(rating_text)
            except:
                pass

            # Title
            title = ""
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, "a[data-hook='review-title']")
                title = title_elem.text.strip()
            except:
                pass

            # Review text
            text = ""
            try:
                text_elem = element.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']")
                text = text_elem.text.strip()
            except:
                pass

            # Date posted
            date_posted = ""
            try:
                date_elem = element.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']")
                date_posted = date_elem.text.strip()
            except:
                pass

            # Helpful count
            helpful_count = 0
            try:
                helpful_elem = element.find_element(By.CSS_SELECTOR, "span[data-hook='helpful-vote-statement']")
                helpful_text = helpful_elem.text.strip()
                helpful_match = re.search(r'(\d+)', helpful_text)
                if helpful_match:
                    helpful_count = int(helpful_match.group(1))
            except:
                pass

            review = {
                'source': self.source_name,
                'author': author,
                'rating': rating,
                'title': title,
                'text': text,
                'date_posted': date_posted,
                'helpful_count': helpful_count,
                'product_url': product_url,
                'product_id': 'Unknown'
            }

            return review

        except Exception as e:
            logging.error(f"[Amazon Selenium] Error parsing review element: {str(e)}")
            return None

    def scrape_product_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape product list from specific page.
        Implements BaseScraper abstract method.
        """
        try:
            url = f"{self.base_url}&page={page}"
            logging.info(f"[Amazon Selenium] Scraping product list from page {page}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Wait for product container to load
            try:
                self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                    )
                )
            except:
                logging.warning(f"[Amazon Selenium] Page {page} took too long to load")
            
            # Extract product elements
            product_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-component-type='s-search-result']"
            )
            
            products = []
            for product_elem in product_elements:
                try:
                    product_data = self._parse_product_element(product_elem)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logging.warning(f"[Amazon Selenium] Error parsing product: {str(e)}")
                    continue
            
            logging.info(f"[Amazon Selenium] Extracted {len(products)} products from page {page}")
            return products
            
        except Exception as e:
            logging.error(f"[Amazon Selenium] Error scraping product list: {str(e)}")
            return []

    def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape detailed information for a specific product.
        Implements BaseScraper abstract method.
        """
        details = {
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None
        }
        
        if not product_url:
            return details
        
        try:
            logging.info(f"[Amazon Selenium] Scraping product details from {product_url}")
            self.driver.get(product_url)
            time.sleep(2)
            
            # Try to find specifications table
            try:
                specs_table = self.driver.find_element(By.CSS_SELECTOR, "table.a-keyvalue")
                rows = specs_table.find_elements(By.CSS_SELECTOR, "tr")
                
                for row in rows:
                    try:
                        key_elem = row.find_element(By.CSS_SELECTOR, "th")
                        val_elem = row.find_element(By.CSS_SELECTOR, "td")
                        
                        key = key_elem.text.strip().lower()
                        val = val_elem.text.strip()
                        
                        if 'peso' in key or 'kg' in key:
                            match = re.search(r'(\d+(?:[,\.]\d+)?)', val)
                            if match:
                                details['kg'] = float(match.group(1).replace(',', '.'))
                        
                        elif 'serbatoio' in key or 'tank' in key:
                            match = re.search(r'(\d+(?:[,\.]\d+)?)', val)
                            if match:
                                details['serbatoio_ml'] = float(match.group(1).replace(',', '.'))
                        
                        elif 'cavo' in key or 'cable' in key or 'cord' in key:
                            match = re.search(r'(\d+)', val)
                            if match:
                                details['cavo_cm'] = int(match.group(1))
                        
                        elif 'watt' in key or 'potenza' in key:
                            match = re.search(r'(\d{3,4})', val)
                            if match:
                                details['potenza_w'] = int(match.group(1))
                        
                        elif 'vapore' in key or 'steam' in key:
                            match = re.search(r'(\d+)', val)
                            if match:
                                details['vapore_setting'] = int(match.group(1))
                        
                        elif 'colore' in key or 'color' in key:
                            details['design_color'] = val[:50]
                        
                        elif 'materiale' in key or 'material' in key:
                            details['design_material'] = val[:50]
                    except:
                        continue
            
            except Exception as e:
                logging.debug(f"[Amazon Selenium] No specs table found: {str(e)}")
            
            # Also try to extract from product title/description
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1 span")
                title = title_elem.text.strip()
                extracted_specs = self._extract_specs_from_title(title)
                
                # Merge with existing details (don't overwrite if already found)
                for key, value in extracted_specs.items():
                    if value and not details[key]:
                        details[key] = value
            except:
                pass
            
            logging.info(f"[Amazon Selenium] Extracted details: {details}")
            return details
            
        except Exception as e:
            logging.error(f"[Amazon Selenium] Error scraping product details: {str(e)}")
            return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape reviews for a product.
        Implements BaseScraper abstract method.
        """
        reviews = []
        
        if not product_url:
            return reviews
        
        try:
            logging.info(f"[Amazon Selenium] Scraping reviews from {product_url}")
            
            self.driver.get(product_url)
            time.sleep(2)
            
            # Scroll to reviews section
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Try to find and click "See more reviews"
            try:
                see_reviews_btn = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']")
                    )
                )
                see_reviews_btn.click()
                time.sleep(3)
            except:
                pass
            
            # Extract review elements
            review_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-hook='review']"
            )
            
            logging.info(f"[Amazon Selenium] Found {len(review_elements)} reviews")
            
            for review_elem in review_elements[:max_reviews]:
                try:
                    review_data = self._parse_review_element(review_elem, product_url)
                    if review_data:
                        reviews.append(review_data)
                except Exception as e:
                    logging.warning(f"[Amazon Selenium] Error parsing review: {str(e)}")
                    continue
            
            logging.info(f"[Amazon Selenium] Extracted {len(reviews)} reviews")
            
        except Exception as e:
            logging.error(f"[Amazon Selenium] Error scraping reviews: {str(e)}")
        
        return reviews

    def close(self):
        """Close the WebDriver"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                logging.info("[Amazon Selenium] Driver closed")
        except Exception as e:
            logging.error(f"[Amazon Selenium] Error closing driver: {str(e)}")

    def __del__(self):
        """Ensure driver is closed when object is destroyed"""
        try:
            self.close()
        except AttributeError:
            # Object not fully initialized
            pass