"""
MEC scraper — uses Playwright to bypass bot protection.
"""
from playwright.sync_api import sync_playwright
from base_scraper import BaseScraper, parse_price

BASE = "https://www.mec.ca"
URL = f"{BASE}/en/products/running/running-and-training-footwear/running-shoes"


class MECScraper(BaseScraper):
    retailer_name = "MEC"
    retailer_website = "https://www.mec.ca"
    retailer_lat = 43.6472
    retailer_lng = -79.3890
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()

            try:
                page.goto(URL, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)

                for _ in range(10):
                    btn = page.query_selector('button[aria-label*="load more"], button:has-text("Load More"), button:has-text("Show more")')
                    if not btn:
                        break
                    btn.click()
                    page.wait_for_timeout(2000)

                cards = page.query_selector_all('[data-testid="product-tile"], .product-tile, article.product-card, [class*="ProductCard"]')
                print(f"[MEC] Found {len(cards)} product cards")

                for card in cards:
                    try:
                        name_el = card.query_selector('[class*="title"], [class*="name"], h3, h4')
                        name = name_el.inner_text().strip() if name_el else ""
                        if not name:
                            continue

                        link_el = card.query_selector("a[href]")
                        href = link_el.get_attribute("href") if link_el else ""
                        url = href if href.startswith("http") else BASE + href

                        img_el = card.query_selector("img")
                        image_url = img_el.get_attribute("src") if img_el else None

                        price_els = card.query_selector_all('[class*="price"], [class*="Price"]')
                        price_texts = [el.inner_text().strip() for el in price_els if el.inner_text().strip()]

                        price = None
                        sale_price = None
                        if len(price_texts) >= 2:
                            price = parse_price(price_texts[0])
                            sale_price = parse_price(price_texts[1])
                        elif len(price_texts) == 1:
                            price = parse_price(price_texts[0])

                        if price is None:
                            continue

                        brand_el = card.query_selector('[class*="brand"], [class*="vendor"]')
                        brand = brand_el.inner_text().strip() if brand_el else ""

                        products.append({
                            "name": name,
                            "brand": brand,
                            "url": url,
                            "image_url": image_url,
                            "price": price,
                            "sale_price": sale_price,
                            "in_stock": True,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[MEC] Product parse error: {e}")

            finally:
                browser.close()

        return products
