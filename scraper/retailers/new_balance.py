"""
New Balance Canada scraper — uses Playwright to bypass bot protection.
"""
from playwright.sync_api import sync_playwright
from base_scraper import BaseScraper, parse_price

BASE = "https://www.newbalance.com"
URL = f"{BASE}/en-CA/mens-running-shoes/?start=0&sz=96"


class NewBalanceScraper(BaseScraper):
    retailer_name = "New Balance"
    retailer_website = "https://www.newbalance.com/en-CA"
    retailer_lat = 43.6532
    retailer_lng = -79.3832
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-CA",
            )
            page = ctx.new_page()

            try:
                page.goto(URL, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)

                consent = page.query_selector('button[id*="accept"], button:has-text("Accept All"), button:has-text("Accept Cookies")')
                if consent:
                    consent.click()
                    page.wait_for_timeout(1000)

                for _ in range(5):
                    more = page.query_selector('button:has-text("Load More"), [data-testid="load-more"]')
                    if not more:
                        break
                    more.click()
                    page.wait_for_timeout(2000)

                cards = page.query_selector_all('.product-tile, [class*="ProductTile"], [class*="product-grid-tile"], li.grid-tile')
                print(f"[New Balance] Found {len(cards)} product cards")

                for card in cards:
                    try:
                        name_el = card.query_selector('.pdp-link a, [class*="product-name"], h3, h4')
                        name = name_el.inner_text().strip() if name_el else ""
                        if not name:
                            continue

                        link_el = card.query_selector("a[href]")
                        href = link_el.get_attribute("href") if link_el else ""
                        url = href if href.startswith("http") else BASE + href

                        img_el = card.query_selector("img[src], img[data-src]")
                        image_url = (img_el.get_attribute("src") or img_el.get_attribute("data-src")) if img_el else None

                        price_el = card.query_selector('[class*="price-standard"], del, [class*="original"]')
                        sale_el = card.query_selector('[class*="price-sales"], [class*="sale-price"], ins')

                        if price_el and sale_el:
                            price = parse_price(price_el.inner_text())
                            sale_price = parse_price(sale_el.inner_text())
                        else:
                            any_price = card.query_selector('[class*="price"]')
                            price = parse_price(any_price.inner_text()) if any_price else None
                            sale_price = None

                        if price is None:
                            continue

                        products.append({
                            "name": name,
                            "brand": "New Balance",
                            "url": url,
                            "image_url": image_url,
                            "price": price,
                            "sale_price": sale_price,
                            "in_stock": True,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[New Balance] Product parse error: {e}")

            finally:
                browser.close()

        return products
