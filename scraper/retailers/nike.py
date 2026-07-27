"""
Nike Canada scraper — high complexity, aggressive bot detection.
Uses Playwright + stealth. Retries up to 2 times before graceful skip.
"""
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS, send_developer_alert

BASE_URL = "https://www.nike.com/ca/w/running-shoes-37v7jzy7ok"
MAX_RETRIES = 2


class NikeScraper(BaseScraper):
    retailer_name = "Nike CA"
    retailer_website = "https://www.nike.com/ca"
    retailer_lat = 43.6532
    retailer_lng = -79.3832
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._do_scrape()
            except Exception as e:
                print(f"[Nike CA] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt == MAX_RETRIES:
                    send_developer_alert(
                        "Nike CA scraper blocked or failed",
                        f"Nike scraper failed after {MAX_RETRIES} attempts: {e}",
                    )
                    return []
                random_delay(8, 15)
        return []

    def _do_scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1366, "height": 768},
                locale="en-CA",
                timezone_id="America/Toronto",
            )
            page = context.new_page()
            stealth_sync(page)

            page.set_extra_http_headers({
                "Accept-Language": "en-CA,en;q=0.9",
                "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            })

            page.goto(BASE_URL, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            if "access denied" in page.title().lower() or "robot" in page.content().lower():
                raise RuntimeError("Nike bot detection triggered")

            # Scroll to load all products (Nike uses infinite scroll)
            last_height = 0
            for _ in range(20):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                random_delay(1, 3)

            cards = page.query_selector_all("[data-testid='product-card'], .product-card__body, .product-grid__card")
            for card in cards:
                try:
                    link = card.query_selector("a[href*='/ca/t/'], a[href*='/product/']")
                    name_el = card.query_selector("[data-testid='product-card__title'], .product-card__title, .product-card__subtitle")
                    price_el = card.query_selector("[data-testid='product-price'] span, .product-price")
                    img_el = card.query_selector("img[src*='static.nike.com'], img[data-src*='static.nike.com']")

                    if not link or not name_el:
                        continue

                    href = link.get_attribute("href") or ""
                    product_url = href if href.startswith("http") else f"https://www.nike.com{href}"
                    image_url = None
                    if img_el:
                        image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src")

                    price_text = price_el.inner_text().strip() if price_el else None

                    products.append({
                        "name": name_el.inner_text().strip(),
                        "brand": "Nike",
                        "url": product_url,
                        "image_url": image_url,
                        "price": price_text,
                        "sale_price": None,
                        "in_stock": True,
                        "category": "road",
                    })
                except Exception as e:
                    print(f"[Nike CA] Card parse error: {e}")

            browser.close()

        return products
