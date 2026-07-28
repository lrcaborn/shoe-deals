"""
MEC scraper — Playwright + stealth. Tries __NEXT_DATA__ first, falls back to DOM.
"""
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, parse_price, USER_AGENTS
import random

BASE = "https://www.mec.ca"
URL = f"{BASE}/en/products/running/running-and-training-footwear/running-shoes"


class MECScraper(BaseScraper):
    retailer_name = "MEC"
    retailer_website = "https://www.mec.ca"
    retailer_lat = 43.6503
    retailer_lng = -79.3924
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

            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            # Try __NEXT_DATA__ (MEC is Next.js)
            next_data = page.evaluate("""() => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? el.textContent : null;
            }""")

            if next_data:
                try:
                    nd = json.loads(next_data)
                    page_props = nd.get("props", {}).get("pageProps", {})
                    raw = (
                        page_props.get("products")
                        or page_props.get("items")
                        or page_props.get("searchResults", {}).get("products")
                        or page_props.get("categoryData", {}).get("products")
                        or []
                    )
                    if raw:
                        for item in raw:
                            try:
                                products.append({
                                    "name": item.get("name") or item.get("title") or "",
                                    "brand": item.get("brand") or item.get("brandName") or "",
                                    "url": BASE + (item.get("url") or item.get("slug") or ""),
                                    "image_url": item.get("image") or item.get("imageUrl"),
                                    "price": item.get("regularPrice") or item.get("originalPrice") or item.get("price"),
                                    "sale_price": item.get("salePrice"),
                                    "in_stock": item.get("inStock", True),
                                    "category": "road",
                                })
                            except Exception as e:
                                print(f"[MEC] __NEXT_DATA__ item error: {e}")

                        if products:
                            browser.close()
                            return products
                except Exception as e:
                    print(f"[MEC] __NEXT_DATA__ parse error: {e}")

            # Load all products via "Load More" or scroll
            for _ in range(15):
                btn = page.query_selector(
                    'button:has-text("Load More"), '
                    'button:has-text("Show More"), '
                    'button[aria-label*="load more"], '
                    '[data-testid="load-more-button"]'
                )
                if not btn:
                    break
                btn.click()
                page.wait_for_timeout(2000)

            cards = page.query_selector_all(
                "[data-testid='product-tile'], "
                "[data-testid='product-card'], "
                ".product-tile, "
                "[class*='ProductCard'], "
                "[class*='product-card'], "
                "article[class*='product'], "
                "li[class*='product']"
            )

            if not cards:
                print(f"[MEC] 0 cards found. Title: {page.title()}")
                html_preview = page.evaluate("() => document.body.innerHTML.substring(0, 3000)")
                print(f"[MEC] HTML preview:\n{html_preview}")
                browser.close()
                return []

            print(f"[MEC] Found {len(cards)} product cards")
            for card in cards:
                try:
                    name_el = card.query_selector("[class*='title'], [class*='name'], h3, h4, h2")
                    name = name_el.inner_text().strip() if name_el else ""
                    if not name:
                        continue

                    link_el = card.query_selector("a[href]")
                    href = link_el.get_attribute("href") if link_el else ""
                    url = href if href.startswith("http") else BASE + href

                    img_el = card.query_selector("img")
                    image_url = img_el.get_attribute("src") if img_el else None

                    price_els = card.query_selector_all("[class*='price'], [class*='Price']")
                    price_texts = [el.inner_text().strip() for el in price_els if el.inner_text().strip()]
                    price = None
                    sale_price = None
                    if len(price_texts) >= 2:
                        price = parse_price(price_texts[0])
                        sale_price = parse_price(price_texts[1])
                    elif len(price_texts) == 1:
                        price = parse_price(price_texts[0])

                    if price is None:
                        continue

                    brand_el = card.query_selector("[class*='brand'], [class*='vendor']")
                    brand = brand_el.inner_text().strip() if brand_el else ""

                    products.append({
                        "name": name,
                        "brand": brand,
                        "url": url,
                        "image_url": image_url,
                        "price": price,
                        "sale_price": sale_price,
                        "in_stock": True,
                        "category": "road",
                    })
                except Exception as e:
                    print(f"[MEC] Product parse error: {e}")

            browser.close()
        return products
