"""
Deletes price_history rows older than 90 days.
Runs daily after scraping to stay within Supabase 50k-row free tier.
"""
from datetime import datetime, timedelta, timezone
from base_scraper import get_supabase


def main():
    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    result = (
        supabase.table("price_history")
        .delete()
        .lt("scraped_at", cutoff)
        .execute()
    )

    deleted = len(result.data) if result.data else 0
    print(f"[cleanup] Deleted {deleted} price_history rows older than 90 days.")


if __name__ == "__main__":
    main()
