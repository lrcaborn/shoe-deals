"""
BlackToe Running scraper — Playwright to fetch Shopify JSON API (bypasses Cloudflare IP block).
"""
import json
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS

COLLECTION = "running-shoes"
BASE = "https://www.blacktoerunning.com"


class BlackToeScraper(BaseScraper):
    retailer_name = "BlackToe Running"
    retailer_website = "https://www.blacktoerunning.com"
    retailer_lat = 43.6444
    retailer_lng = -79.4028
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

            pg = 1
            while True:
                url = f"{BASE}/collections/{COLLECTION}/products.json?limit=250&page={pg}"
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                text = page.evaluate("() => document.body.innerText")
                try:
                    data = json.loads(text).get("products", [])
                except Exception:
                    print(f"[BlackToe Running] JSON parse failed on page {pg}")
                    break
                if not data:
                    break

                for item in data:
                    try:
                        variant = next((v for v in item["variants"] if v.get("available")), item["variants"][0] if item["variants"] else None)
                        if not variant:
                            continue
                        price = variant.get("compare_at_price") or variant.get("price")
                        sale_price = variant.get("price") if variant.get("compare_at_price") else None
                        image_url = item["images"][0]["src"] if item.get("images") else None
                        products.append({
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
                        print(f"[BlackToe Running] Product parse error: {e}")

                if len(data) < 250:
                    break
                pg += 1
                random_delay()

            browser.close()
        return products
