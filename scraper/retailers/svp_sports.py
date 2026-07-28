"""
SVP Sports scraper — uses Shopify JSON API.
"""
import random
import httpx
from base_scraper import BaseScraper, random_delay, http_get_with_retry, USER_AGENTS

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
        random_delay(3, 6)

        # Try known collection handles in order
        for collection in ["running", "running-shoes", "footwear-running", "footwear"]:
            page = 1
            with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
                while True:
                    url = f"{BASE}/collections/{collection}/products.json?limit=250&page={page}"
                    try:
                        resp = http_get_with_retry(client, url)
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 404:
                            break
                        raise
                    data = resp.json().get("products", [])
                    if not data:
                        break

                    for p in data:
                        try:
                            ptype = (p.get("product_type") or "").lower()
                            tags = " ".join(p.get("tags") or []).lower()
                            if not any(kw in ptype or kw in tags or kw in p["title"].lower()
                                       for kw in ["running", "shoe", "footwear"]):
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

            if products:
                break

        return products
