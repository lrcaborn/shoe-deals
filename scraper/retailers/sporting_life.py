"""
Sporting Life scraper — medium complexity, uses httpx + BeautifulSoup.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://www.sportinglife.ca/en-CA/footwear/running-shoes"


class SportingLifeScraper(BaseScraper):
    retailer_name = "Sporting Life"
    retailer_website = "https://www.sportinglife.ca"
    retailer_lat = 43.6850
    retailer_lng = -79.4010
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        page = 1

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE_URL}?start={(page - 1) * 48}&sz=48"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".product-tile, [class*='product-tile'], .product-grid-tile")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a.thumb-link, a[data-pid], a[href*='/footwear/']")
                        name_el = card.select_one(".product-name, .tile-name, h3.name")
                        brand_el = card.select_one(".brand, .tile-brand")
                        price_el = card.select_one(".price-sales, .sale-price, .now-price")
                        orig_el = card.select_one(".price-standard, .original-price, .was-price")
                        img_el = card.select_one("img.primary-image, img[data-src], .product-image img")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        product_url = href if href.startswith("http") else f"https://www.sportinglife.ca{href}"
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

                # Stop if fewer results than a full page
                if len(cards) < 48:
                    break
                page += 1
                random_delay()

        return products
