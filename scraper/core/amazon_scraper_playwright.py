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

        # Power (Potenza) - "2400W", "2400 W", "2400 watt"
        power_match = re.search(r'(\d{3,4})\s*W(?:att)?', title, re.IGNORECASE)
        if power_match:
            specs['potenza_w'] = int(power_match.group(1))
            logging.debug(f"[Amazon] Title: Potenza {specs['potenza_w']}W")

        # Weight (Kg) - "1.2 kg", "1,2 Chilogrammi"
        kg_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(?:kg|chilogrammi?)', title, re.IGNORECASE)
        if kg_match:
            specs['kg'] = float(kg_match.group(1).replace(',', '.'))
            logging.debug(f"[Amazon] Title: Peso {specs['kg']}kg")

        # Tank (Serbatoio) - "300ml", "1.5L", "da 1,8L", "serbatoio 200ml"
        tank_match = re.search(r'(?:da\s+|serbatoio\s+)?(\d+(?:[,\.]\d+)?)\s*([mlL]+)', title, re.IGNORECASE)
        if tank_match:
            tank_val = float(tank_match.group(1).replace(',', '.'))
            # Convert liters to ml
            if tank_match.group(2).lower() in ['l', 'l']:
                tank_val = tank_val * 1000
            specs['serbatoio_ml'] = tank_val
            logging.debug(f"[Amazon] Title: Serbatoio {specs['serbatoio_ml']}ml")

        # Cable/Cord (Cavo) - "cavo 180 cm", "180cm"
        cord_match = re.search(r'(?:cavo\s+)?(\d+)\s*cm', title, re.IGNORECASE)
        if cord_match:
            specs['cavo_cm'] = int(cord_match.group(1))
            logging.debug(f"[Amazon] Title: Cavo {specs['cavo_cm']}cm")

        # Steam output (Vapore) - "500g/min", "120 g", "colpo vapore 240g"
        steam_match = re.search(r'(\d+)\s*g(?:/min)?', title, re.IGNORECASE)
        if steam_match:
            specs['vapore_setting'] = int(steam_match.group(1))
            logging.debug(f"[Amazon] Title: Vapore {specs['vapore_setting']}g/min")

        # Design material keywords
        if any(mat in title.lower() for mat in ['steamglide', 'ceramica', 'ceramic']):
            specs['design_material'] = 'ceramica'
        elif any(mat in title.lower() for mat in ['inox', 'acciaio', 'stainless']):
            specs['design_material'] = 'inox'
        elif 'antiaderente' in title.lower():
            specs['design_material'] = 'antiaderente'

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

            # Get full page text for fallback regex extraction
            page_text = await page_obj.content()
            logging.info(f"[Amazon] Page text length: {len(page_text)}")

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
                            
                            # ===== PESO / KG (FIXED) =====
                            if 'peso' in key and 'dell' in key:  # "Peso dell'articolo"
                                # Pattern: "1,2 Chilogrammi" or "1.2 kg"
                                peso_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(chilogrammi|chilogrammo|kg|g)', val, re.IGNORECASE)
                                if peso_match:
                                    peso_val = float(peso_match.group(1).replace(',', '.'))
                                    unit = peso_match.group(2).lower()
                                    # Only convert from grams if explicitly "g" (not "chilogrammi" or "kg")
                                    if unit == 'g':
                                        peso_val = peso_val / 1000
                                    details['kg'] = peso_val
                                    logging.info(f"[Amazon] Extracted Peso: {details['kg']} kg from '{val}'")
                            
                            # ===== SERBATOIO / TANK (IMPROVED) =====
                            elif 'serbatoio' in key or 'tank' in key:
                                # Pattern: "1.5 L" or "300 ml" or "1,5 litri"
                                tank_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*([mlL]+|litri?)', val, re.IGNORECASE)
                                if tank_match:
                                    tank_val = float(tank_match.group(1).replace(',', '.'))
                                    unit = tank_match.group(2).lower()
                                    # Convert liters to ml if unit is L or litri
                                    if unit in ['l', 'litri', 'litro', 'litri']:
                                        tank_val = tank_val * 1000
                                    elif unit in ['ml', 'cc']:  # already in ml
                                        pass
                                    details['serbatoio_ml'] = tank_val
                                    logging.info(f"[Amazon] Extracted Serbatoio: {details['serbatoio_ml']} ml from '{val}'")
                            
                            # ===== VAPORE / STEAM FLOW (IMPROVED) =====
                            elif 'vapore' in key or 'steam' in key:
                                # Pattern: "120 g/min" or "500 g" or "30g/min"
                                vapor_match = re.search(r'(\d+)\s*(?:g(?:/min)?)', val, re.IGNORECASE)
                                if vapor_match:
                                    details['vapore_setting'] = int(vapor_match.group(1))
                                    logging.info(f"[Amazon] Extracted Vapore: {details['vapore_setting']} g/min from '{val}'")
                            
                            # ===== POTENZA / POWER (IMPROVED) =====
                            elif 'watt' in key or 'potenza' in key or 'power' in key:
                                # Pattern: "2400 W" or "2400W" or "2400"
                                power_match = re.search(r'(\d{3,4})\s*[wW]?', val)
                                if power_match:
                                    details['potenza_w'] = int(power_match.group(1))
                                    logging.info(f"[Amazon] Extracted Potenza: {details['potenza_w']} W from '{val}'")
                            
                            # ===== CAVO / CABLE LENGTH =====
                            elif 'cavo' in key or 'cable' in key or 'cord' in key:
                                # Pattern: "180 cm" or "1.8 m" or "180cm"
                                cable_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(cm|m(?!m))', val, re.IGNORECASE)
                                if cable_match:
                                    cable_val = float(cable_match.group(1).replace(',', '.'))
                                    # Convert meters to cm if needed
                                    if cable_match.group(2).lower() == 'm':
                                        cable_val = cable_val * 100
                                    details['cavo_cm'] = int(cable_val)
                                    logging.info(f"[Amazon] Extracted Cavo: {details['cavo_cm']} cm from '{val}'")
                            
                            # ===== DESIGN MATERIAL =====
                            elif 'piastra' in key or 'plate' in key or 'rivestimento' in key:
                                if any(mat in val.lower() for mat in ['ceramica', 'ceramic']):
                                    details['design_material'] = 'ceramica'
                                elif any(mat in val.lower() for mat in ['inox', 'stainless', 'acciaio']):
                                    details['design_material'] = 'inox'
                                elif any(mat in val.lower() for mat in ['antiaderente', 'non-stick']):
                                    details['design_material'] = 'antiaderente'
                                logging.info(f"[Amazon] Material: {details['design_material']} from '{val}'")
                                
                    except Exception as e:
                        logging.debug(f"[Amazon] Row parse error: {str(e)}")
                        continue
            except Exception as e:
                logging.warning(f"[Amazon] Table parsing failed: {str(e)}")

            # ===== FALLBACK: Extract from page text using regex =====
            if not details['kg']:
                # Pattern: "Peso dell'articolo   1,2 Chilogrammi" or similar
                peso_match = re.search(r'Peso\s+dell[.\']articolo\s+([0-9,\.]+)\s*(Chilogrammi|chilogrammi|kg|g)', page_text)
                if peso_match:
                    peso_val = float(peso_match.group(1).replace(',', '.'))
                    unit = peso_match.group(2).lower()
                    # Only convert if explicitly "g" (not "kg" or "chilogrammi")
                    if unit == 'g':
                        peso_val = peso_val / 1000
                    details['kg'] = peso_val
                    logging.info(f"[Amazon] Fallback extracted Peso: {details['kg']} kg from '{peso_match.group(0)}'")

            if not details['serbatoio_ml']:
                # Pattern: "Serbatoio: 300ml", "Serbatoio da 1.5L", "da 1,5L", etc.
                serbatoio_match = re.search(r'(?:[Ss]erbatoio|tank|da)\s*[:\s]*([0-9,\.]+)\s*([mlL]+|litri?)', page_text, re.IGNORECASE)
                if serbatoio_match:
                    tank_val = float(serbatoio_match.group(1).replace(',', '.'))
                    unit = serbatoio_match.group(2).lower()
                    # Convert liters to ml if needed
                    if unit in ['l', 'litri', 'litro', 'litri']:
                        tank_val = tank_val * 1000
                    details['serbatoio_ml'] = tank_val
                    logging.info(f"[Amazon] Fallback extracted Serbatoio: {details['serbatoio_ml']} ml from '{serbatoio_match.group(0)}'")

            if not details['potenza_w']:
                potenza_match = re.search(r'[Pp]otenza[:\s]+(\d{3,4})\s*[wW]?', page_text)
                if potenza_match:
                    details['potenza_w'] = int(potenza_match.group(1))
                    logging.info(f"[Amazon] Fallback extracted Potenza: {details['potenza_w']} W")

            if not details['vapore_setting']:
                # Look for "colpo vapore" or "vapore continuo"
                vapore_match = re.search(r'[Cc]olpo\s+[Vv]apore[:\s]+(\d+)\s*g(?:/min)?', page_text)
                if vapore_match:
                    details['vapore_setting'] = int(vapore_match.group(1))
                    logging.info(f"[Amazon] Fallback extracted Vapore: {details['vapore_setting']} g/min")

        except Exception as e:
            logging.error(f"[Amazon] Detail error: {str(e)}")
            import traceback
            logging.error(f"[Amazon] Traceback: {traceback.format_exc()}")
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
            logging.info(f"[Amazon] Reviews page loaded, waiting for review elements...")
            await page_obj.wait_for_timeout(2000)

            # CRITICAL: Wait for review elements to actually load before parsing
            try:
                await page_obj.wait_for_selector("div[data-hook='review']", timeout=10000)
                logging.info(f"[Amazon] Review elements detected, loading complete")
            except:
                logging.warning(f"[Amazon] Timeout waiting for review elements, continuing anyway")

            # Scroll to load more reviews
            await page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page_obj.wait_for_timeout(2000)

            # Try to click "See all reviews" if available
            try:
                see_reviews = await page_obj.query_selector("a[data-hook='see-all-reviews-link-foot']")
                if see_reviews:
                    logging.info(f"[Amazon] Clicking 'See all reviews' link...")
                    await see_reviews.click()
                    await page_obj.wait_for_timeout(3000)
            except:
                pass

            logging.info(f"[Amazon] Looking for review elements...")
            review_divs = await page_obj.query_selector_all("div[data-hook='review']")
            logging.info(f"[Amazon] Found {len(review_divs)} review elements")

            # DEBUG: Save the HTML of the first review for inspection
            if review_divs and len(review_divs) > 0:
                try:
                    first_review_html = await review_divs[0].evaluate("el => el.outerHTML")
                    with open("debug_review_html.txt", "w", encoding="utf-8") as f:
                        f.write(first_review_html)
                    logging.info(f"[Amazon] Saved first review HTML to debug_review_html.txt")
                except:
                    pass

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
                else:
                    # Try alternative selector for review text
                    text_elem = await element.query_selector("div.a-row.a-spacing-small span")
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