"""
Sport Chek scraper — Playwright + stealth. Tries __NEXT_DATA__ first, falls back to DOM.
"""
import json
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from base_scraper import BaseScraper, random_delay, USER_AGENTS, parse_price

# Sport Chek dropped the .html suffix in their replatform
URLS_TO_TRY = [
    "https://www.sportchek.ca/categories/footwear/running-shoes/",
    "https://www.sportchek.ca/categories/footwear/running-shoes.html",
    "https://www.sportchek.ca/en/footwear/running-shoes/",
]


class SportChekScraper(BaseScraper):
    retailer_name = "Sport Chek"
    retailer_website = "https://www.sportchek.ca"
    retailer_lat = 43.6534
    retailer_lng = -79.3803
    retailer_city = "Toronto"

    def scrape(self) -> list[dict]:
        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 900},
            )
            page = ctx.new_page()
            stealth_sync(page)

            # Find the first URL that loads products
            working_url = None
            for url in URLS_TO_TRY:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                if page.url.startswith("https://www.sportchek.ca") and "404" not in page.title().lower():
                    working_url = page.url
                    break

            if not working_url:
                print("[Sport Chek] Could not find a valid category URL")
                browser.close()
                return []

            page_num = 1
            while True:
                if page_num > 1:
                    page.goto(f"{working_url}?page={page_num}", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                # Try __NEXT_DATA__ first (Next.js sites embed products in page JSON)
                next_data = page.evaluate("""() => {
                    const el = document.getElementById('__NEXT_DATA__');
                    return el ? el.textContent : null;
                }""")

                if next_data:
                    try:
                        nd = json.loads(next_data)
                        # Navigate common Next.js product paths
                        page_props = nd.get("props", {}).get("pageProps", {})
                        raw_products = (
                            page_props.get("products")
                            or page_props.get("items")
                            or page_props.get("data", {}).get("products")
                            or page_props.get("categoryProducts", {}).get("products")
                            or []
                        )
                        if raw_products:
                            for item in raw_products:
                                try:
                                    products.append({
                                        "name": item.get("name") or item.get("title") or "",
                                        "brand": item.get("brand") or item.get("brandName") or "",
                                        "url": "https://www.sportchek.ca" + (item.get("url") or item.get("pdpUrl") or ""),
                                        "image_url": item.get("imageUrl") or item.get("image"),
                                        "price": item.get("originalPrice") or item.get("regularPrice") or item.get("price"),
                                        "sale_price": item.get("salePrice") or item.get("currentPrice"),
                                        "in_stock": item.get("inStock", True),
                                        "category": "road",
                                    })
                                except Exception as e:
                                    print(f"[Sport Chek] __NEXT_DATA__ item parse error: {e}")

                            # Check if there's a next page
                            has_next = page_props.get("hasNextPage") or len(raw_products) >= 24
                            if not has_next:
                                break
                            page_num += 1
                            random_delay()
                            continue
                    except Exception as e:
                        print(f"[Sport Chek] __NEXT_DATA__ parse error: {e}")

                # DOM fallback
                cards = page.query_selector_all(
                    "[data-testid='product-card'], "
                    ".product-card, "
                    ".product-list-item, "
                    "[class*='ProductCard'], "
                    "[class*='product-card'], "
                    "li[class*='product']"
                )

                if not cards:
                    # Diagnostic: dump page info so we can debug selectors
                    print(f"[Sport Chek] 0 cards found. Title: {page.title()}")
                    print(f"[Sport Chek] URL: {page.url}")
                    html_preview = page.evaluate("() => document.body.innerHTML.substring(0, 3000)")
                    print(f"[Sport Chek] HTML preview:\n{html_preview}")
                    break

                for card in cards:
                    try:
                        name_el = card.query_selector("[class*='product-name'], [data-testid='product-name'], h3, h2")
                        brand_el = card.query_selector("[class*='brand'], [data-testid='brand']")
                        price_el = card.query_selector("[class*='sale-price'], [class*='current-price'], [data-testid='price'], [class*='price']")
                        orig_el = card.query_selector("[class*='original-price'], [class*='was-price'], [data-testid='original-price'], del")
                        link_el = card.query_selector("a")
                        img_el = card.query_selector("img")

                        if not name_el or not link_el:
                            continue

                        href = link_el.get_attribute("href") or ""
                        url = href if href.startswith("http") else f"https://www.sportchek.ca{href}"
                        image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src") if img_el else None
                        sale_text = price_el.inner_text() if price_el else None
                        orig_text = orig_el.inner_text() if orig_el else None

                        products.append({
                            "name": name_el.inner_text().strip(),
                            "brand": brand_el.inner_text().strip() if brand_el else "",
                            "url": url,
                            "image_url": image_url,
                            "price": orig_text or sale_text,
                            "sale_price": sale_text if orig_text else None,
                            "in_stock": True,
                            "category": "road",
                        })
                    except Exception as e:
                        print(f"[Sport Chek] Card parse error: {e}")

                next_btn = page.query_selector("[aria-label='Next page'], [data-testid='pagination-next']:not([disabled]), a[rel='next']")
                if not next_btn:
                    break
                page_num += 1
                random_delay()

            browser.close()
        return products
