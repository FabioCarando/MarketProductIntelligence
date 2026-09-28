# -*- coding: utf-8 -*-
"""Debug: Capture product page HTML to inspect specs location"""

import asyncio
from playwright.async_api import async_playwright

async def debug_product_page():
    """Capture first product page HTML"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    try:
        # Use a real product URL from Amazon.it
        product_url = "https://www.amazon.it/Imetec-Tecnologia-Anticalcare-Risparmio-Energetico/dp/B07CKY9SNZ"
        
        print(f"[DEBUG] Navigating to: {product_url}")
        await page.goto(product_url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Save full HTML
        html = await page.content()
        with open("debug_product_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"[DEBUG] Saved full product page HTML to debug_product_page.html")
        
        # Try to find specifications
        try:
            # Look for spec tables
            spec_tables = await page.query_selector_all("table")
            print(f"[DEBUG] Found {len(spec_tables)} tables on page")
            
            # Look for specific elements
            details_section = await page.query_selector("div[data-feature-name]")
            if details_section:
                print(f"[DEBUG] Found details section with data-feature-name")
            
            # Save a snippet of key sections
            with open("debug_product_snippets.txt", "w", encoding="utf-8") as f:
                # Look for text containing keywords
                page_text = await page.evaluate("() => document.body.innerText")
                
                # Extract lines with keywords
                lines = page_text.split('\n')
                f.write("=== LINES CONTAINING KEY SPECS ===\n\n")
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['kg', 'peso', 'watt', 'vapore', 'serbatoio', 'cavo', 'lunghezza', 'potenza']):
                        f.write(line + '\n')
            
            print(f"[DEBUG] Saved snippets to debug_product_snippets.txt")
            
        except Exception as e:
            print(f"[DEBUG] Error inspecting: {str(e)}")
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_product_page())