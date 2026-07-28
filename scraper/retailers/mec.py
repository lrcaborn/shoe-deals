"""
MEC scraper — medium complexity, httpx + BeautifulSoup.
Filters to running shoes only.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://www.mec.ca/en/c/running-shoes"


class MECScraper(BaseScraper):
    retailer_name = "MEC"
    retailer_website = "https://www.mec.ca"
    retailer_lat = 43.6449
    retailer_lng = -79.3985
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
        }
        page = 1

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE_URL}?page={page}"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select("[class*='ProductCard'], .product-card, [data-testid*='product']")
                if not cards:
                    # Try alternate selectors for MEC's layout
                    cards = soup.select("li.product-list-item, .product-grid-item")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a[href*='/en/product/']")
                        name_el = card.select_one("[class*='product-name'], [class*='ProductName'], h3")
                        brand_el = card.select_one("[class*='brand'], [class*='Brand']")
                        price_el = card.select_one("[class*='sale-price'], [class*='price-sale'], [class*='currentPrice']")
                        orig_el = card.select_one("[class*='original-price'], [class*='was-price'], [class*='regularPrice']")
                        img_el = card.select_one("img")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        product_url = href if href.startswith("http") else f"https://www.mec.ca{href}"
                        image_url = None
                        if img_el:
                            image_url = img_el.get("src") or img_el.get("data-src")

                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": brand_el.get_text(strip=True) if brand_el else "",
                            "url": product_url,
                            "image_url": image_url,
                            "price": orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None,
                            "sale_price": price_el.get_text(strip=True) if orig_el else None,
                            "in_stock": card.select_one("[class*='sold-out'], [class*='outOfStock']") is None,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[MEC] Card parse error: {e}")

                if len(cards) < 48:
                    break
                page += 1
                random_delay()

        return products
