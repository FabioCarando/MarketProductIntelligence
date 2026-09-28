import asyncio
from playwright.async_api import async_playwright

async def debug():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    url = "https://www.amazon.it/Imetec-Tecnologia-Anticalcare-Risparmio-Energetico/dp/B07CKY9SNZ"
    
    print(f"Navigating to {url}...")
    await page.goto(url, wait_until="load", timeout=60000)
    await page.wait_for_timeout(2000)
    
    # Get FULL HTML
    html = await page.content()
    
    with open("debug_full_html.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Full HTML saved to debug_full_html.html")
    
    # Also search for KG and CAVO specifically
    html_lower = html.lower()
    
    if 'kg' in html_lower:
        print("✅ Found 'kg' in HTML")
        # Find context around kg
        idx = html_lower.find('kg')
        print(f"Context: ...{html[max(0,idx-100):idx+100]}...")
    else:
        print("❌ NOT found 'kg' in HTML")
    
    if 'cavo' in html_lower:
        print("✅ Found 'cavo' in HTML")
        idx = html_lower.find('cavo')
        print(f"Context: ...{html[max(0,idx-100):idx+100]}...")
    else:
        print("❌ NOT found 'cavo' in HTML")
    
    await page.close()
    await context.close()
    await browser.close()
    await playwright.stop()

asyncio.run(debug())