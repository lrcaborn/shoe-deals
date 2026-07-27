"""
Sport Chek scraper — JS-heavy, uses Playwright.
Filters to running shoes category.
"""
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://www.sportchek.ca/categories/footwear/running-shoes.html"


class SportChekScraper(BaseScraper):
    retailer_name = "Sport Chek"
    retailer_website = "https://www.sportchek.ca"
    retailer_lat = 43.6461
    retailer_lng = -79.3802
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            stealth_sync(page)

            page_num = 1
            while True:
                url = f"{BASE_URL}?page={page_num}"
                page.goto(url, timeout=30000, wait_until="networkidle")

                cards = page.query_selector_all("[data-testid='product-card'], .product-card, .product-list-item")
                if not cards:
                    break

                for card in cards:
                    try:
                        name_el = card.query_selector("[class*='product-name'], [data-testid='product-name'], h3")
                        brand_el = card.query_selector("[class*='brand'], [data-testid='brand']")
                        price_el = card.query_selector("[class*='sale-price'], [class*='current-price'], [data-testid='price']")
                        orig_el = card.query_selector("[class*='original-price'], [class*='was-price'], [data-testid='original-price']")
                        link_el = card.query_selector("a")
                        img_el = card.query_selector("img")

                        if not name_el or not link_el:
                            continue

                        name = name_el.inner_text().strip()
                        brand = brand_el.inner_text().strip() if brand_el else ""
                        href = link_el.get_attribute("href") or ""
                        url = href if href.startswith("http") else f"https://www.sportchek.ca{href}"
                        image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src") if img_el else None

                        sale_price_text = price_el.inner_text() if price_el else None
                        orig_price_text = orig_el.inner_text() if orig_el else None

                        if orig_price_text:
                            price = orig_price_text
                            sale_price = sale_price_text
                        else:
                            price = sale_price_text
                            sale_price = None

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
                        print(f"[Sport Chek] Card parse error: {e}")

                # Check for next page
                next_btn = page.query_selector("[aria-label='Next page'], [data-testid='pagination-next']:not([disabled])")
                if not next_btn:
                    break
                page_num += 1
                random_delay()

            browser.close()

        return products
