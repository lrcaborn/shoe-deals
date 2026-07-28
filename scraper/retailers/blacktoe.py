"""
BlackToe Running scraper — uses Shopify JSON API.
"""
import random
import httpx
from base_scraper import BaseScraper, random_delay, http_get_with_retry, USER_AGENTS

COLLECTION = "running-shoes"
BASE = "https://www.blacktoerunning.com"


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
        random_delay(3, 6)

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE}/collections/{COLLECTION}/products.json?limit=250&page={page}"
                resp = http_get_with_retry(client, url)
                data = resp.json().get("products", [])
                if not data:
                    break

                for p in data:
                    try:
                        variant = next((v for v in p["variants"] if v.get("available")), p["variants"][0] if p["variants"] else None)
                        if not variant:
                            continue
                        price = variant.get("compare_at_price") or variant.get("price")
                        sale_price = variant.get("price") if variant.get("compare_at_price") else None
                        image_url = p["images"][0]["src"] if p.get("images") else None
                        products.append({
                            "name": p["title"],
                            "brand": p.get("vendor", ""),
                            "url": f"{BASE}/products/{p['handle']}",
                            "image_url": image_url,
                            "price": price,
                            "sale_price": sale_price,
                            "in_stock": any(v.get("available") for v in p["variants"]),
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[BlackToe Running] Product parse error: {e}")

                if len(data) < 250:
                    break
                page += 1
                random_delay()

        return products
