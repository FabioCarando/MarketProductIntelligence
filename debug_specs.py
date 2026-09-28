import asyncio
from playwright.async_api import async_playwright

async def debug():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    # Product URL
    url = "https://www.amazon.it/Imetec-Tecnologia-Anticalcare-Risparmio-Energetico/dp/B07CKY9SNZ"
    
    print(f"Navigating to {url}...")
    await page.goto(url, wait_until="load", timeout=60000)
    await page.wait_for_timeout(2000)
    
    # Get all text
    text = await page.evaluate("() => document.body.innerText")
    
    # Save ONLY lines with key specs
    with open("debug_all_specs.txt", "w", encoding="utf-8") as f:
        for line in text.split('\n'):
            if any(kw in line.lower() for kw in ['watt', 'kg', 'peso', 'cavo', 'lunghezza', 'vapore', 'g/min', 'serbatoio', 'piastra', 'materiale', 'design']):
                f.write(line + '\n')
    
    print("✅ Saved to debug_all_specs.txt")
    
    await page.close()
    await context.close()
    await browser.close()
    await playwright.stop()

asyncio.run(debug())