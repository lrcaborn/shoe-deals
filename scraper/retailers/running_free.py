"""
Running Free scraper — uses httpx + BeautifulSoup.
Scrapes both men's and women's running shoe categories.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE = "https://www.runningfree.com"
CATEGORY_URLS = [
    f"{BASE}/products/All-Mens-66507/Shoes-27/Running-28/",
    f"{BASE}/products/All-Womens-66508/Shoes-27/Running-28/",
]


class RunningFreeScraper(BaseScraper):
    retailer_name = "Running Free"
    retailer_website = "https://www.runningfree.com"
    retailer_lat = 43.7615
    retailer_lng = -79.3300
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        seen_urls = set()
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            for category_url in CATEGORY_URLS:
                page = 1
                while True:
                    url = f"{category_url}?p={page}" if page > 1 else category_url
                    resp = client.get(url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    cards = soup.select(".product-item, [class*='product-item-info'], .product-list-item")
                    if not cards:
                        break

                    found_new = False
                    for card in cards:
                        try:
                            link = card.select_one("a.product-item-link, a[href*='/products/']")
                            name_el = card.select_one(".product-item-name a, .product-item-name, .product-name")
                            brand_el = card.select_one(".brand, [class*='brand']")
                            price_el = card.select_one(".special-price .price, .price-box .price")
                            orig_el = card.select_one(".old-price .price")
                            img_el = card.select_one("img.product-image-photo, img[data-src]")

                            if not link or not name_el:
                                continue

                            href = link.get("href", "")
                            product_url = href if href.startswith("http") else f"{BASE}{href}"

                            if product_url in seen_urls:
                                continue
                            seen_urls.add(product_url)
                            found_new = True

                            products.append({
                                "name": name_el.get_text(strip=True),
                                "brand": brand_el.get_text(strip=True) if brand_el else "",
                                "url": product_url,
                                "image_url": img_el.get("src") or img_el.get("data-src") if img_el else None,
                                "price": orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None,
                                "sale_price": price_el.get_text(strip=True) if orig_el else None,
                                "in_stock": card.select_one(".out-of-stock") is None,
                                "category": "road",
                            })
                        except Exception as e:
                            print(f"[Running Free] Card parse error: {e}")

                    if not found_new or len(cards) < 20:
                        break
                    page += 1
                    random_delay()

        return products
