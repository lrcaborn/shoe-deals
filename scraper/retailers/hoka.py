"""
HOKA scraper — Playwright + stealth. Waits explicitly for product tiles to load.
"""
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS, send_developer_alert, parse_price

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
                result = self._do_scrape()
                if result:
                    return result
                print(f"[HOKA] Attempt {attempt}/{MAX_RETRIES} returned 0 products")
                if attempt < MAX_RETRIES:
                    random_delay(5, 10)
            except Exception as e:
                print(f"[HOKA] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt == MAX_RETRIES:
                    send_developer_alert("HOKA scraper blocked or failed", str(e))
                    return []
                random_delay(5, 10)
        return []

    def _do_scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 900},
                locale="en-CA",
                timezone_id="America/Toronto",
            )
            page = ctx.new_page()
            stealth_sync(page)
            page.set_extra_http_headers({
                "Accept-Language": "en-CA,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            })

            page_num = 1
            while True:
                url = f"{BASE_URL}?start={(page_num - 1) * 24}&sz=24"
                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                # Check for Cloudflare challenge
                if "just a moment" in page.title().lower():
                    raise RuntimeError("Cloudflare challenge detected")

                # Wait explicitly for product content — HOKA lazy-loads via JS
                try:
                    page.wait_for_selector(
                        ".product-tile, [class*='ProductTile'], [class*='product-tile'], "
                        "[data-component*='product'], [class*='tile-body']",
                        timeout=10000
                    )
                except PlaywrightTimeout:
                    print(f"[HOKA] Timed out waiting for product tiles on page {page_num}")
                    print(f"[HOKA] Title: {page.title()}")
                    html_preview = page.evaluate("() => document.body.innerHTML.substring(0, 3000)")
                    print(f"[HOKA] HTML preview:\n{html_preview}")
                    break

                cards = page.query_selector_all(
                    ".product-tile, "
                    "[class*='ProductTile'], "
                    "[class*='product-tile'], "
                    "[data-component*='product'], "
                    "[class*='tile-body']"
                )
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.query_selector("a[href]")
                        name_el = card.query_selector(
                            "[class*='product-name'], [class*='ProductName'], "
                            "[class*='tile-name'], h3, h4, h2"
                        )
                        if not link or not name_el:
                            continue

                        href = link.get_attribute("href") or ""
                        product_url = href if href.startswith("http") else f"https://www.hoka.com{href}"
                        img_el = card.query_selector("img")
                        image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src") if img_el else None

                        price_el = card.query_selector(
                            "[class*='sale-price'], [class*='price-sales'], "
                            "[class*='current-price'], [class*='price']:not([class*='original'])"
                        )
                        orig_el = card.query_selector(
                            "[class*='original-price'], [class*='price-standard'], "
                            "[class*='was-price'], del, s"
                        )

                        products.append({
                            "name": name_el.inner_text().strip(),
                            "brand": "HOKA",
                            "url": product_url,
                            "image_url": image_url,
                            "price": parse_price(orig_el.inner_text()) if orig_el else parse_price(price_el.inner_text() if price_el else None),
                            "sale_price": parse_price(price_el.inner_text()) if orig_el and price_el else None,
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
