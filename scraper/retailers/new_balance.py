"""
New Balance Canada scraper — medium complexity, httpx + BeautifulSoup.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://www.newbalance.com/en-ca/running-shoes/"


class NewBalanceScraper(BaseScraper):
    retailer_name = "New Balance CA"
    retailer_website = "https://www.newbalance.com/en-ca"
    retailer_lat = 43.6532
    retailer_lng = -79.3832
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-CA,en;q=0.9",
        }
        start = 0
        page_size = 48

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE_URL}?start={start}&sz={page_size}"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".product-tile, [class*='product-tile'], .grid-tile")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a.thumb-link, a.product-tile__link")
                        name_el = card.select_one(".product-tile__title, .product-name")
                        price_el = card.select_one(".product-tile__pricing .sales .value, .price-sales")
                        orig_el = card.select_one(".product-tile__pricing .strike-through .value, .price-standard")
                        img_el = card.select_one("img.product-tile__image, img[data-src]")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        product_url = href if href.startswith("http") else f"https://www.newbalance.com{href}"
                        image_url = None
                        if img_el:
                            image_url = img_el.get("src") or img_el.get("data-src")

                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": "New Balance",
                            "url": product_url,
                            "image_url": image_url,
                            "price": orig_el.get("content") or orig_el.get_text(strip=True) if orig_el else price_el.get("content") or price_el.get_text(strip=True) if price_el else None,
                            "sale_price": price_el.get("content") or price_el.get_text(strip=True) if orig_el else None,
                            "in_stock": card.select_one(".product-tile__availability--unavailable") is None,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[New Balance CA] Card parse error: {e}")

                if len(cards) < page_size:
                    break
                start += page_size
                random_delay()

        return products
