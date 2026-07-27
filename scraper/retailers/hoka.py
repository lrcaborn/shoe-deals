"""
HOKA scraper — high complexity, Cloudflare protection.
Uses Playwright + stealth. Retries up to 2 times before graceful skip.
"""
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS, send_developer_alert

BASE_URL = "https://www.hoka.com/en-ca/running/"
MAX_RETRIES = 2


class HokaScraper(BaseScraper):
    retailer_name = "HOKA"
    retailer_website = "https://www.hoka.com/en-ca"
    retailer_lat = 43.6532
    retailer_lng = -79.3832
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._do_scrape()
            except Exception as e:
                print(f"[HOKA] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt == MAX_RETRIES:
                    send_developer_alert(
                        "HOKA scraper blocked or failed",
                        f"HOKA scraper failed after {MAX_RETRIES} attempts: {e}",
                    )
                    return []
                random_delay(5, 10)
        return []

    def _do_scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 900},
                locale="en-CA",
                timezone_id="America/Toronto",
            )
            page = context.new_page()
            stealth_sync(page)

            # Add extra headers to appear more legitimate
            page.set_extra_http_headers({
                "Accept-Language": "en-CA,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            })

            page_num = 1
            while True:
                url = f"{BASE_URL}?start={(page_num - 1) * 24}&sz=24"
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                # Check for Cloudflare challenge page
                if "just a moment" in page.title().lower() or "cloudflare" in page.content().lower():
                    raise RuntimeError("Cloudflare challenge detected")

                cards = page.query_selector_all(".product-tile, [class*='ProductTile'], [data-componentname*='product']")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.query_selector("a")
                        name_el = card.query_selector("[class*='product-name'], [class*='ProductName']")
                        price_el = card.query_selector("[class*='sale-price'], [class*='price-sales'], [class*='currentPrice']")
                        orig_el = card.query_selector("[class*='original-price'], [class*='price-standard']")
                        img_el = card.query_selector("img")

                        if not link or not name_el:
                            continue

                        href = link.get_attribute("href") or ""
                        product_url = href if href.startswith("http") else f"https://www.hoka.com{href}"
                        image_url = None
                        if img_el:
                            image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src")

                        products.append({
                            "name": name_el.inner_text().strip(),
                            "brand": "HOKA",
                            "url": product_url,
                            "image_url": image_url,
                            "price": orig_el.inner_text().strip() if orig_el else name_el.inner_text().strip(),
                            "sale_price": price_el.inner_text().strip() if orig_el and price_el else None,
                            "in_stock": not card.query_selector("[class*='sold-out'], [class*='out-of-stock']"),
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[HOKA] Card parse error: {e}")

                if len(cards) < 24:
                    break
                page_num += 1
                random_delay(3, 7)

            browser.close()

        return products
