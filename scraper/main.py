"""
Main entry point: runs all retailer scrapers sequentially.
"""
import sys
from retailers.sport_chek import SportChekScraper
from retailers.sporting_life import SportingLifeScraper
from retailers.running_room import RunningRoomScraper
from retailers.blacktoe import BlackToeScraper
from retailers.runners_shop import RunnersShopScraper
from retailers.running_free import RunningFreeScraper
from retailers.svp_sports import SVPSportsScraper
from retailers.mec import MECScraper
from retailers.new_balance import NewBalanceScraper
from retailers.hoka import HokaScraper
from retailers.nike import NikeScraper
from retailers.culture_athletics import CultureAthleticsScraper

SCRAPERS = [
    SportChekScraper,
    SportingLifeScraper,
    RunningRoomScraper,
    BlackToeScraper,
    RunnersShopScraper,
    RunningFreeScraper,
    SVPSportsScraper,
    MECScraper,
    NewBalanceScraper,
    HokaScraper,
    NikeScraper,
    CultureAthleticsScraper,
]


def main():
    results = {}
    for ScraperClass in SCRAPERS:
        scraper = ScraperClass()
        count = scraper.run()
        results[scraper.retailer_name] = count

    print("\n=== Scrape Summary ===")
    total = 0
    for name, count in results.items():
        status = "OK" if count > 0 else "ZERO"
        print(f"  [{status}] {name}: {count} products")
        total += count
    print(f"  Total: {total} products scraped")

    zero_count = sum(1 for c in results.values() if c == 0)
    if zero_count > 0:
        print(f"\nWARNING: {zero_count} scraper(s) returned 0 products.")
        sys.exit(1)


if __name__ == "__main__":
    main()
