"""
SVP Sports scraper — uses Shopify JSON API.
"""
import random
import httpx
from base_scraper import BaseScraper, random_delay, USER_AGENTS

COLLECTION = "running"
BASE = "https://www.svpsports.ca"


class SVPSportsScraper(BaseScraper):
    retailer_name = "SVP Sports"
    retailer_website = "https://www.svpsports.ca"
    retailer_lat = 43.7731
    retailer_lng = -79.4144
    retailer_city = "North York"

    def scrape(self) -> list[dict]:
        products = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        page = 1

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            while True:
                url = f"{BASE}/collections/{COLLECTION}/products.json?limit=250&page={page}"
                resp = client.get(url)
                if resp.status_code == 404:
                    # Try alternate collection handle
                    url = f"{BASE}/collections/running-shoes/products.json?limit=250&page={page}"
                    resp = client.get(url)
                resp.raise_for_status()
                data = resp.json().get("products", [])
                if not data:
                    break

                for p in data:
                    try:
                        # Filter to running shoes by checking product type or tags
                        tags = [t.lower() for t in p.get("tags", [])]
                        ptype = (p.get("product_type") or "").lower()
                        if not any(kw in ptype or kw in " ".join(tags) for kw in ["running", "shoe", "footwear"]):
                            if not any(kw in p["title"].lower() for kw in ["shoe", "runner", "running"]):
                                continue

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
                        print(f"[SVP Sports] Product parse error: {e}")

                if len(data) < 250:
                    break
                page += 1
                random_delay()

        return products
