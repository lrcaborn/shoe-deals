"""
Sporting Life scraper — uses httpx + BeautifulSoup.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE = "https://www.sportinglife.ca"
CATEGORY_URL = f"{BASE}/en-CA/running/footwear/"


class SportingLifeScraper(BaseScraper):
    retailer_name = "Sporting Life"
    retailer_website = "https://www.sportinglife.ca"
    retailer_lat = 43.7116
    retailer_lng = -79.3975
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        start = 0
        page_size = 48

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{CATEGORY_URL}?start={start}&sz={page_size}"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".product-tile, [class*='product-tile'], .product-grid-tile")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a.thumb-link, a[data-pid], a[href*='/footwear/'], a[href*='/running/']")
                        name_el = card.select_one(".product-name, .tile-name, h3.name")
                        brand_el = card.select_one(".brand, .tile-brand")
                        price_el = card.select_one(".price-sales, .sale-price, .now-price")
                        orig_el = card.select_one(".price-standard, .original-price, .was-price")
                        img_el = card.select_one("img.primary-image, img[data-src], .product-image img")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        product_url = href if href.startswith("http") else f"{BASE}{href}"
                        image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": brand_el.get_text(strip=True) if brand_el else "",
                            "url": product_url,
                            "image_url": image_url,
                            "price": orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None,
                            "sale_price": price_el.get_text(strip=True) if orig_el else None,
                            "in_stock": "out-of-stock" not in card.get("class", []),
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[Sporting Life] Card parse error: {e}")

                if len(cards) < page_size:
                    break
                start += page_size
                random_delay()

        return products
