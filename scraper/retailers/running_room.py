"""
Running Room scraper — medium complexity, httpx + BeautifulSoup.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://shop.runningroom.com/en-ca/running-shoes"


class RunningRoomScraper(BaseScraper):
    retailer_name = "Running Room"
    retailer_website = "https://shop.runningroom.com"
    retailer_lat = 43.6629
    retailer_lng = -79.3957
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        page = 1

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE_URL}?p={page}"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".product-item, .product-card, [class*='product-item-info']")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a.product-item-link, a[href*='/running-shoes/']")
                        name_el = card.select_one(".product-item-name, .product-name")
                        brand_el = card.select_one(".product-brand, .brand-name")
                        price_el = card.select_one(".price-wrapper .price, .special-price .price")
                        orig_el = card.select_one(".old-price .price, .regular-price")
                        img_el = card.select_one("img.product-image-photo, img.product-img")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": brand_el.get_text(strip=True) if brand_el else "",
                            "url": href if href.startswith("http") else f"https://shop.runningroom.com{href}",
                            "image_url": image_url,
                            "price": orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None,
                            "sale_price": price_el.get_text(strip=True) if orig_el else None,
                            "in_stock": card.select_one(".out-of-stock") is None,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[Running Room] Card parse error: {e}")

                if len(cards) < 20:
                    break
                page += 1
                random_delay()

        return products
