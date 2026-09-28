# -*- coding: utf-8 -*-
"""
Amazon.it Scraper using Playwright - Fixed version
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from base_scraper import BaseScraper


class AmazonPlaywrightScraper(BaseScraper):
    """Scraper for Amazon.it using Playwright"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Amazon scraper"""
        self.source_name = "Amazon.it"
        self.base_url = "https://www.amazon.it/s?k=ferro+da+stiro"
        super().__init__(self.source_name, config)

    def _ensure_absolute_url(self, url: str) -> str:
        """Convert relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return f"https://www.amazon.it{url}"
        return f"https://www.amazon.it/{url}"

    def scrape_product_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """Scrape product list"""
        try:
            return asyncio.run(self._scrape_product_list_async(page))
        except Exception as e:
            logging.error(f"[Amazon] Error: {str(e)}")
            return []

    async def _scrape_product_list_async(self, page: int = 1) -> List[Dict[str, Any]]:
        """Async scrape product list"""
        products = []
        
        if async_playwright is None:
            logging.error("[Amazon] Playwright not installed")
            return []
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page_obj = await context.new_page()
        
        try:
            url = f"{self.base_url}&page={page}"
            logging.info(f"[Amazon] Scraping page {page}")
            
            await page_obj.goto(url, wait_until="load", timeout=60000)
            await page_obj.wait_for_timeout(3000)
            
            product_divs = await page_obj.query_selector_all("div[data-component-type='s-search-result']")
            logging.info(f"[Amazon] Found {len(product_divs)} products")
            
            for product_div in product_divs:
                try:
                    product_data = await self._parse_product_element_async(product_div)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logging.debug(f"[Amazon] Parse error: {str(e)}")
                    
        except Exception as e:
            logging.error(f"[Amazon] Scrape error: {str(e)}")
        finally:
            await page_obj.close()
            await context.close()
            await browser.close()
            await playwright.stop()
        
        logging.info(f"[Amazon] Extracted {len(products)} products")
        return products

    async def _parse_product_element_async(self, element) -> Optional[Dict[str, Any]]:
        """Parse product element"""
        try:
            name = "Unknown"
            try:
                name_elem = await element.query_selector("h2 span")
                if name_elem:
                    name = (await name_elem.text_content()).strip()
            except:
                pass

            url = ""
            try:
                link_elem = await element.query_selector("h2 a")
                if link_elem:
                    url = await link_elem.get_attribute("href")
                    url = self._ensure_absolute_url(url)
                else:
                    # Try alternative selector for Amazon product links
                    link_elem = await element.query_selector("a[href*='/dp/']")
                    if link_elem:
                        url = await link_elem.get_attribute("href")
                        url = self._ensure_absolute_url(url)
            except:
                pass

            price = None
            try:
                price_elem = await element.query_selector("span.a-price-whole")
                if price_elem:
                    price_text = (await price_elem.text_content()).strip()
                    price = self._extract_price(price_text)
            except:
                pass

            rating = None
            try:
                rating_elem = await element.query_selector("span.a-icon-star-small span")
                if rating_elem:
                    rating_text = await rating_elem.text_content()
                    rating = float(rating_text.split()[0])
            except:
                pass

            review_count = 0
            try:
                review_elem = await element.query_selector("span[aria-label*='valutazioni']")
                if review_elem:
                    review_text = (await review_elem.text_content()).strip()
                    match = re.search(r'(\d+)', review_text.split()[0])
                    if match:
                        review_count = int(match.group(1))
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

            product.update(self._extract_specs_from_title(name))
            return product

        except Exception as e:
            logging.error(f"[Amazon] Parse error: {str(e)}")
            return None

    def _extract_specs_from_title(self, title: str) -> Dict[str, Any]:
        """Extract specs from title"""
        specs = {}

        power_match = re.search(r'(\d{3,4})\s*W(?:att)?', title, re.IGNORECASE)
        if power_match:
            specs['potenza_w'] = int(power_match.group(1))

        kg_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*kg', title, re.IGNORECASE)
        if kg_match:
            specs['kg'] = float(kg_match.group(1).replace(',', '.'))

        tank_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(?:ml|cc)', title, re.IGNORECASE)
        if tank_match:
            specs['serbatoio_ml'] = float(tank_match.group(1).replace(',', '.'))

        cord_match = re.search(r'cavo\s+(\d+)\s*cm', title, re.IGNORECASE)
        if cord_match:
            specs['cavo_cm'] = int(cord_match.group(1))

        steam_match = re.search(r'(\d+)\s*impostazioni?\s+vapore', title, re.IGNORECASE)
        if steam_match:
            specs['vapore_setting'] = int(steam_match.group(1))

        return specs

    def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """Scrape product details"""
        logging.info(f"[Amazon] SCRAPING DETAILS for: {product_url[:80]}...")
        try:
            result = asyncio.run(self._scrape_product_details_async(product_url))
            logging.info(f"[Amazon] Details result: {result}")
            return result
        except Exception as e:
            logging.error(f"[Amazon] Details ERROR: {str(e)}")
            import traceback
            logging.error(f"[Amazon] Traceback: {traceback.format_exc()}")
            return {}

    async def _scrape_product_details_async(self, product_url: str) -> Dict[str, Any]:
        """Async scrape product details"""
        details = {
            'kg': None,
            'serbatoio_ml': None,
            'cavo_cm': None,
            'vapore_setting': None,
            'potenza_w': None,
            'design_color': None,
            'design_material': None
        }

        if not product_url or async_playwright is None:
            logging.warning(f"[Amazon] Missing URL or Playwright: url={bool(product_url)}, pw={async_playwright is not None}")
            return details

        logging.info(f"[Amazon] Opening browser for details...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page_obj = await context.new_page()
        
        try:
            product_url = self._ensure_absolute_url(product_url)
            logging.info(f"[Amazon] Navigating to: {product_url[:100]}...")
            await page_obj.goto(product_url, wait_until="load", timeout=60000)
            logging.info(f"[Amazon] Page loaded, waiting for content...")
            await page_obj.wait_for_timeout(2000)

            try:
                logging.info(f"[Amazon] Looking for specs table...")
                specs_rows = await page_obj.query_selector_all("table.a-keyvalue tr")
                logging.info(f"[Amazon] Found {len(specs_rows)} spec rows")
                for row in specs_rows:
                    try:
                        key_elem = await row.query_selector("th")
                        val_elem = await row.query_selector("td")
                        
                        if key_elem and val_elem:
                            key = (await key_elem.text_content()).strip().lower()
                            val = (await val_elem.text_content()).strip()
                            
                            if 'peso' in key or 'kg' in key:
                                match = re.search(r'(\d+(?:[,\.]\d+)?)', val)
                                if match:
                                    details['kg'] = float(match.group(1).replace(',', '.'))
                            
                            elif 'serbatoio' in key or 'tank' in key:
                                match = re.search(r'(\d+(?:[,\.]\d+)?)', val)
                                if match:
                                    details['serbatoio_ml'] = float(match.group(1).replace(',', '.'))
                            
                            elif 'cavo' in key or 'cable' in key:
                                match = re.search(r'(\d+)', val)
                                if match:
                                    details['cavo_cm'] = int(match.group(1))
                            
                            elif 'watt' in key or 'potenza' in key:
                                match = re.search(r'(\d{3,4})', val)
                                if match:
                                    details['potenza_w'] = int(match.group(1))
                            
                            elif 'vapore' in key:
                                match = re.search(r'(\d+)', val)
                                if match:
                                    details['vapore_setting'] = int(match.group(1))
                    except:
                        continue
            except:
                pass

        except Exception as e:
            logging.error(f"[Amazon] Detail error: {str(e)}")
        finally:
            await page_obj.close()
            await context.close()
            await browser.close()
            await playwright.stop()

        return details

    def scrape_reviews(self, product_url: str, max_reviews: int = 5) -> List[Dict[str, Any]]:
        """Scrape reviews"""
        logging.info(f"[Amazon] SCRAPING REVIEWS for: {product_url[:80]}... (max: {max_reviews})")
        try:
            result = asyncio.run(self._scrape_reviews_async(product_url, max_reviews))
            logging.info(f"[Amazon] Reviews result: {len(result)} reviews extracted")
            return result
        except Exception as e:
            logging.error(f"[Amazon] Reviews ERROR: {str(e)}")
            import traceback
            logging.error(f"[Amazon] Traceback: {traceback.format_exc()}")
            return []

    async def _scrape_reviews_async(self, product_url: str, max_reviews: int = 5) -> List[Dict[str, Any]]:
        """Async scrape reviews"""
        reviews = []

        if not product_url or async_playwright is None:
            logging.warning(f"[Amazon] Missing URL or Playwright for reviews")
            return reviews

        logging.info(f"[Amazon] Opening browser for reviews...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page_obj = await context.new_page()
        
        try:
            product_url = self._ensure_absolute_url(product_url)
            logging.info(f"[Amazon] Navigating to reviews page...")
            await page_obj.goto(product_url, wait_until="load", timeout=60000)
            logging.info(f"[Amazon] Reviews page loaded, scrolling...")
            await page_obj.wait_for_timeout(2000)

            await page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page_obj.wait_for_timeout(2000)

            try:
                see_reviews = await page_obj.query_selector("a[data-hook='see-all-reviews-link-foot']")
                if see_reviews:
                    await see_reviews.click()
                    await page_obj.wait_for_timeout(3000)
            except:
                pass

            logging.info(f"[Amazon] Looking for review elements...")
            review_divs = await page_obj.query_selector_all("div[data-hook='review']")
            logging.info(f"[Amazon] Found {len(review_divs)} review elements")

            for idx, review_div in enumerate(review_divs[:max_reviews]):
                try:
                    review_data = await self._parse_review_element_async(review_div, product_url)
                    if review_data:
                        reviews.append(review_data)
                except Exception as e:
                    logging.debug(f"[Amazon] Review parse error: {str(e)}")

        except Exception as e:
            logging.error(f"[Amazon] Review scrape error: {str(e)}")
        finally:
            await page_obj.close()
            await context.close()
            await browser.close()
            await playwright.stop()

        logging.info(f"[Amazon] Extracted {len(reviews)} reviews")
        return reviews

    async def _parse_review_element_async(self, element, product_url: str) -> Optional[Dict[str, Any]]:
        """Parse review element"""
        try:
            author = "Anonymous"
            try:
                author_elem = await element.query_selector(".a-profile-name")
                if author_elem:
                    author = (await author_elem.text_content()).strip()
            except:
                pass

            rating = None
            try:
                rating_elem = await element.query_selector("span[data-hook='review-star-rating'] span")
                if rating_elem:
                    rating_text = await rating_elem.text_content()
                    rating = float(rating_text.split()[0])
            except:
                pass

            title = ""
            try:
                title_elem = await element.query_selector("a[data-hook='review-title']")
                if title_elem:
                    title = (await title_elem.text_content()).strip()
            except:
                pass

            text = ""
            try:
                text_elem = await element.query_selector("span[data-hook='review-body']")
                if text_elem:
                    text = (await text_elem.text_content()).strip()
            except:
                pass

            date_posted = ""
            try:
                date_elem = await element.query_selector("span[data-hook='review-date']")
                if date_elem:
                    date_posted = (await date_elem.text_content()).strip()
            except:
                pass

            helpful_count = 0
            try:
                helpful_elem = await element.query_selector("span[data-hook='helpful-vote-statement']")
                if helpful_elem:
                    helpful_text = await helpful_elem.text_content()
                    match = re.search(r'(\d+)', helpful_text)
                    if match:
                        helpful_count = int(match.group(1))
            except:
                pass

            return {
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

        except Exception as e:
            logging.error(f"[Amazon] Review parse error: {str(e)}")
            return None

    def close(self):
        """Close scraper"""
        logging.info("[Amazon] Scraper closed")