"""
Base scraper class with shared logic for all retailer scrapers.
"""
import os
import random
import time
import re
from abc import ABC, abstractmethod
from supabase import create_client, Client
import resend


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
DEVELOPER_ALERT_EMAIL = os.environ.get("DEVELOPER_ALERT_EMAIL", "")

resend.api_key = RESEND_API_KEY

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
]

BRAND_NORMALIZATIONS = {
    "hoka one one": "HOKA",
    "hoka oneone": "HOKA",
    "new balance": "New Balance",
    "nb": "New Balance",
    "on running": "On",
    "on cloudsurfer": "On",
    "brooks running": "Brooks",
    "asics": "ASICS",
    "salomon": "Salomon",
    "altra": "Altra",
    "saucony": "Saucony",
    "mizuno": "Mizuno",
    "newton running": "Newton",
}


def normalize_brand(brand: str) -> str:
    if not brand:
        return brand
    lower = brand.lower().strip()
    return BRAND_NORMALIZATIONS.get(lower, brand.strip())


def parse_price(price_str: str) -> float | None:
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(price_str))
    try:
        return float(cleaned)
    except ValueError:
        return None


def random_delay(min_s: float = 2.0, max_s: float = 5.0):
    time.sleep(random.uniform(min_s, max_s))


def http_get_with_retry(client, url: str, max_retries: int = 3, backoff: float = 10.0):
    """GET with retry on 429/5xx. Raises on final failure."""
    import httpx
    for attempt in range(1, max_retries + 1):
        resp = client.get(url)
        if resp.status_code == 429:
            wait = backoff * attempt
            print(f"  429 on {url} — waiting {wait}s before retry {attempt}/{max_retries}")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    raise Exception(f"Failed after {max_retries} retries: {url}")


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def send_developer_alert(subject: str, body: str):
    if not DEVELOPER_ALERT_EMAIL or not RESEND_API_KEY:
        print(f"[ALERT] {subject}: {body}")
        return
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": DEVELOPER_ALERT_EMAIL,
            "subject": subject,
            "text": body,
        })
    except Exception as e:
        print(f"Failed to send developer alert: {e}")


class BaseScraper(ABC):
    retailer_name: str
    retailer_website: str
    retailer_lat: float
    retailer_lng: float
    retailer_city: str = "Toronto"

    def __init__(self):
        self.supabase = get_supabase()
        self._retailer_id: str | None = None

    @property
    def retailer_id(self) -> str:
        if self._retailer_id is None:
            result = (
                self.supabase.table("retailers")
                .select("id")
                .eq("name", self.retailer_name)
                .single()
                .execute()
            )
            self._retailer_id = result.data["id"]
        return self._retailer_id

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Returns a list of product dicts with keys:
          name, brand, url, image_url, price, sale_price, in_stock, category
        """
        ...

    def run(self) -> int:
        print(f"[{self.retailer_name}] Starting scrape...")
        try:
            products = self.scrape()
        except Exception as e:
            print(f"[{self.retailer_name}] Scrape failed: {e}")
            send_developer_alert(
                f"Scraper failure: {self.retailer_name}",
                f"Scraper raised an exception: {e}",
            )
            return 0

        count = 0
        for p in products:
            try:
                self._upsert_product(p)
                count += 1
            except Exception as e:
                print(f"[{self.retailer_name}] Failed to upsert {p.get('url')}: {e}")

        print(f"[{self.retailer_name}] Scraped {count} products.")

        if count == 0:
            send_developer_alert(
                f"Zero products scraped: {self.retailer_name}",
                f"The scraper for {self.retailer_name} returned 0 products. "
                f"Check for site layout changes.",
            )

        return count

    def _upsert_product(self, p: dict):
        brand = normalize_brand(p.get("brand") or "")
        price = parse_price(p.get("price"))
        sale_price = parse_price(p.get("sale_price"))

        if price is None:
            raise ValueError(f"Could not parse price for {p.get('url')}")

        # Upsert product row (match on retailer_id + url)
        product_result = (
            self.supabase.table("products")
            .upsert(
                {
                    "retailer_id": self.retailer_id,
                    "name": p["name"].strip(),
                    "brand": brand,
                    "category": p.get("category", "road"),
                    "url": p["url"],
                    "image_url": p.get("image_url"),
                },
                on_conflict="retailer_id,url",
            )
            .execute()
        )

        product_id = product_result.data[0]["id"]

        # Always insert a new price_history row
        self.supabase.table("price_history").insert(
            {
                "product_id": product_id,
                "price": price,
                "sale_price": sale_price,
                "in_stock": bool(p.get("in_stock", True)),
            }
        ).execute()
