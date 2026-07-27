"""
BlackToe Running scraper — low-medium complexity, httpx + BeautifulSoup.
Shopify-based store.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE_URL = "https://www.blacktoerunning.com/collections/running-shoes"


class BlackToeScraper(BaseScraper):
    retailer_name = "BlackToe Running"
    retailer_website = "https://www.blacktoerunning.com"
    retailer_lat = 43.6465
    retailer_lng = -79.4042
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        page = 1

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE_URL}?page={page}"
                resp = client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".product-item, .grid__item, [class*='product-card']")
                if not cards:
                    break

                for card in cards:
                    try:
                        link = card.select_one("a[href*='/products/']")
                        name_el = card.select_one(".product-item__title, .product__title, h3")
                        brand_el = card.select_one(".product-item__vendor, .vendor")
                        price_el = card.select_one(".price__regular .price-item, .product-price__price")
                        orig_el = card.select_one(".price__compare .price-item, .price--compare")
                        img_el = card.select_one("img[src*='cdn.shopify'], img[data-src*='cdn.shopify']")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        product_url = href if href.startswith("http") else f"https://www.blacktoerunning.com{href}"
                        image_url = None
                        if img_el:
                            src = img_el.get("src") or img_el.get("data-src") or ""
                            image_url = src if src.startswith("http") else f"https:{src}"

                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": brand_el.get_text(strip=True) if brand_el else "",
                            "url": product_url,
                            "image_url": image_url,
                            "price": orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None,
                            "sale_price": price_el.get_text(strip=True) if orig_el else None,
                            "in_stock": "sold-out" not in " ".join(card.get("class", [])),
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[BlackToe Running] Card parse error: {e}")

                if len(cards) < 24:
                    break
                page += 1
                random_delay()

        return products
