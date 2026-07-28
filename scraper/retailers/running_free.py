"""
Running Free scraper — httpx + BeautifulSoup.
Scrapes both men's and women's running shoe categories and deduplicates.
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
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9",
        }

        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            for category_url in CATEGORY_URLS:
                page = 1
                while True:
                    url = category_url if page == 1 else f"{category_url}?page={page}"
                    resp = client.get(url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Running Free uses a variety of possible product container patterns
                    cards = (
                        soup.select(".listing-container .products-grid .product-item")
                        or soup.select(".products-grid .item")
                        or soup.select(".product-list .product-item")
                        or soup.select(".productListing .productListingItem")
                        or soup.select("[class*='product-item']")
                        or soup.select("[class*='listing-item']")
                    )

                    if not cards and page == 1:
                        # Diagnostic: dump what we got
                        print(f"[Running Free] 0 cards found at {url}")
                        print(f"[Running Free] Status: {resp.status_code}")
                        print(f"[Running Free] HTML preview:\n{resp.text[:2000]}")
                        break

                    if not cards:
                        break

                    found_new = False
                    for card in cards:
                        try:
                            link = (
                                card.select_one("a.product-item-link")
                                or card.select_one("a[href*='/products/']")
                                or card.select_one(".product-name a")
                                or card.select_one("h3 a, h4 a, h2 a")
                                or card.select_one("a")
                            )
                            name_el = (
                                card.select_one(".product-item-name")
                                or card.select_one(".product-name")
                                or card.select_one("h3, h4, h2")
                            )
                            price_el = (
                                card.select_one(".special-price .price")
                                or card.select_one(".price-box .price")
                                or card.select_one("[class*='price']")
                            )
                            orig_el = card.select_one(".old-price .price, .regular-price .price")
                            img_el = card.select_one("img")

                            if not link or not name_el:
                                continue

                            href = link.get("href", "")
                            product_url = href if href.startswith("http") else f"{BASE}{href}"

                            if product_url in seen_urls:
                                continue
                            seen_urls.add(product_url)
                            found_new = True

                            name = name_el.get_text(strip=True)
                            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None
                            price_text = orig_el.get_text(strip=True) if orig_el else price_el.get_text(strip=True) if price_el else None
                            sale_text = price_el.get_text(strip=True) if orig_el else None

                            products.append({
                                "name": name,
                                "brand": "",
                                "url": product_url,
                                "image_url": image_url,
                                "price": price_text,
                                "sale_price": sale_text,
                                "in_stock": card.select_one(".out-of-stock, .unavailable") is None,
                                "category": "road",
                            })
                        except Exception as e:
                            print(f"[Running Free] Card parse error: {e}")

                    if not found_new or len(cards) < 20:
                        break
                    page += 1
                    random_delay()

        return products
