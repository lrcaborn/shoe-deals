"""
New Balance Canada scraper — Playwright + stealth. Tries several URL patterns.
"""
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, parse_price, USER_AGENTS

BASE = "https://www.newbalance.com"
# Try multiple URL formats — NB CA has changed their URL structure
URLS_TO_TRY = [
    f"{BASE}/en-CA/running-shoes/",
    f"{BASE}/en-CA/mens-running-shoes/?start=0&sz=96",
    f"{BASE}/en-CA/running/",
]


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
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 800},
                locale="en-CA",
            )
            page = ctx.new_page()
            stealth_sync(page)

            working_url = None
            for url in URLS_TO_TRY:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                if "404" not in page.title().lower() and page.url != "https://www.newbalance.com/en-CA/":
                    working_url = page.url
                    break

            if not working_url:
                print("[New Balance] No valid URL found")
                browser.close()
                return []

            # Accept cookies if present
            consent = page.query_selector('button[id*="accept"], button:has-text("Accept All"), button:has-text("Accept Cookies")')
            if consent:
                consent.click()
                page.wait_for_timeout(1000)

            # Load more products
            for _ in range(5):
                more = page.query_selector(
                    'button:has-text("Load More"), '
                    '[data-testid="load-more"], '
                    'button[aria-label*="more products"]'
                )
                if not more:
                    break
                more.click()
                page.wait_for_timeout(2000)

            cards = page.query_selector_all(
                ".product-tile, "
                "[class*='ProductTile'], "
                "[class*='product-grid-tile'], "
                "li.grid-tile, "
                "[class*='product-item'], "
                "[data-component='product-tile']"
            )

            if not cards:
                print(f"[New Balance] 0 cards found. Title: {page.title()}")
                html_preview = page.evaluate("() => document.body.innerHTML.substring(0, 3000)")
                print(f"[New Balance] HTML preview:\n{html_preview}")
                browser.close()
                return []

            print(f"[New Balance] Found {len(cards)} product cards")
            for card in cards:
                try:
                    name_el = card.query_selector(".pdp-link a, [class*='product-name'], [class*='ProductName'], h3, h4")
                    name = name_el.inner_text().strip() if name_el else ""
                    if not name:
                        continue

                    link_el = card.query_selector("a[href]")
                    href = link_el.get_attribute("href") if link_el else ""
                    url = href if href.startswith("http") else BASE + href

                    img_el = card.query_selector("img[src], img[data-src]")
                    image_url = (img_el.get_attribute("src") or img_el.get_attribute("data-src")) if img_el else None

                    price_el = card.query_selector("[class*='price-standard'], del, [class*='original'], [class*='was']")
                    sale_el = card.query_selector("[class*='price-sales'], [class*='sale-price'], ins, [class*='current']")

                    if price_el and sale_el:
                        price = parse_price(price_el.inner_text())
                        sale_price = parse_price(sale_el.inner_text())
                    else:
                        any_price = card.query_selector("[class*='price']")
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

            browser.close()
        return products
