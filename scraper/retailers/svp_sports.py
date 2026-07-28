"""
SVP Sports scraper — Playwright to fetch Shopify JSON API (bypasses Cloudflare IP block).
"""
import json
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS

BASE = "https://www.svpsports.ca"
COLLECTIONS = ["running", "running-shoes", "footwear-running", "footwear"]


class SVPSportsScraper(BaseScraper):
    retailer_name = "SVP Sports"
    retailer_website = "https://www.svpsports.ca"
    retailer_lat = 43.7099
    retailer_lng = -79.4516
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            stealth_sync(page)

            for collection in COLLECTIONS:
                pg = 1
                collection_products = []
                while True:
                    url = f"{BASE}/collections/{collection}/products.json?limit=250&page={pg}"
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    text = page.evaluate("() => document.body.innerText")
                    try:
                        data = json.loads(text).get("products", [])
                    except Exception:
                        break
                    if not data:
                        break

                    for item in data:
                        try:
                            ptype = (item.get("product_type") or "").lower()
                            tags = " ".join(item.get("tags") or []).lower()
                            if not any(kw in ptype or kw in tags or kw in item["title"].lower()
                                       for kw in ["running", "shoe", "footwear"]):
                                continue

                            variant = next((v for v in item["variants"] if v.get("available")), item["variants"][0] if item["variants"] else None)
                            if not variant:
                                continue
                            price = variant.get("compare_at_price") or variant.get("price")
                            sale_price = variant.get("price") if variant.get("compare_at_price") else None
                            image_url = item["images"][0]["src"] if item.get("images") else None
                            collection_products.append({
                                "name": item["title"],
                                "brand": item.get("vendor", ""),
                                "url": f"{BASE}/products/{item['handle']}",
                                "image_url": image_url,
                                "price": price,
                                "sale_price": sale_price,
                                "in_stock": any(v.get("available") for v in item["variants"]),
                                "category": "road",
                            })
                        except Exception as e:
                            print(f"[SVP Sports] Product parse error: {e}")

                    if len(data) < 250:
                        break
                    pg += 1
                    random_delay()

                if collection_products:
                    products = collection_products
                    break

            browser.close()
        return products
