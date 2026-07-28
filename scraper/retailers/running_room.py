"""
Running Room scraper — httpx + BeautifulSoup.
Running Room blocks datacenter IPs at the origin; this scraper will likely return 0
until we either get a residential proxy or find a workaround. Fails gracefully.
"""
import random
import httpx
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE = "https://www.runningroom.com"
URLS_TO_TRY = [
    f"{BASE}/en-ca/running-shoes",
    f"{BASE}/en-ca/c/running-shoes",
    f"{BASE}/en-ca/footwear/running-shoes",
]


class RunningRoomScraper(BaseScraper):
    retailer_name = "Running Room"
    retailer_website = "https://www.runningroom.com"
    retailer_lat = 43.6629
    retailer_lng = -79.3957
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9",
        }

        working_url = None
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            for url in URLS_TO_TRY:
                try:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        working_url = url
                        first_resp = resp
                        break
                except Exception as e:
                    print(f"[Running Room] {url} → {e}")
                    continue

        if not working_url:
            print("[Running Room] All URLs failed (site may be blocking datacenter IPs)")
            return []

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            page = 1
            resp = first_resp
            while True:
                soup = BeautifulSoup(resp.text, "lxml")
                cards = (
                    soup.select(".product-item, [class*='product-item-info']")
                    or soup.select(".product-card, .product-list-item")
                    or soup.select("[class*='product-card']")
                )

                if not cards and page == 1:
                    print(f"[Running Room] 0 cards at {working_url}")
                    print(f"[Running Room] HTML preview:\n{resp.text[:2000]}")
                    break

                if not cards:
                    break

                for card in cards:
                    try:
                        link = (
                            card.select_one("a.product-item-link")
                            or card.select_one("a[href*='/running-shoes/']")
                            or card.select_one("a")
                        )
                        name_el = card.select_one(".product-item-name, .product-name, h3, h4")
                        brand_el = card.select_one(".product-brand, .brand-name")
                        price_el = card.select_one(".price-wrapper .price, .special-price .price, [class*='price']")
                        orig_el = card.select_one(".old-price .price, .regular-price")
                        img_el = card.select_one("img")

                        if not link or not name_el:
                            continue

                        href = link.get("href", "")
                        products.append({
                            "name": name_el.get_text(strip=True),
                            "brand": brand_el.get_text(strip=True) if brand_el else "",
                            "url": href if href.startswith("http") else f"{BASE}{href}",
                            "image_url": img_el.get("src") or img_el.get("data-src") if img_el else None,
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
                try:
                    resp = client.get(f"{working_url}?p={page}")
                    resp.raise_for_status()
                except Exception as e:
                    print(f"[Running Room] Page {page} failed: {e}")
                    break

        return products
