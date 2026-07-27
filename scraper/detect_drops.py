"""
Post-scrape price drop detection.
Compares the two most recent price_history rows per product,
identifies drops, and sends batched alert emails via Resend.
"""
import os
from collections import defaultdict
from base_scraper import get_supabase, send_developer_alert
import resend

resend.api_key = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = "alerts@gtarunningdeals.ca"
DROP_THRESHOLD_PCT = 20.0


def format_price(price: float) -> str:
    return f"${price:.2f} CAD"


def format_pct(pct: float) -> str:
    return f"{pct:.0f}%"


def main():
    supabase = get_supabase()

    # Fetch all products
    products_resp = supabase.table("products").select("id,name,url").execute()
    products = {p["id"]: p for p in products_resp.data}

    # user_id -> list of alert dicts
    user_alerts: dict[str, list[dict]] = defaultdict(list)

    for product_id, product in products.items():
        # Get 2 most recent price_history rows
        hist = (
            supabase.table("price_history")
            .select("price,sale_price,scraped_at")
            .eq("product_id", product_id)
            .order("scraped_at", desc=True)
            .limit(2)
            .execute()
        )

        if len(hist.data) < 2:
            continue

        current_row = hist.data[0]
        previous_row = hist.data[1]

        current_price = float(current_row["sale_price"] or current_row["price"])
        previous_price = float(previous_row["sale_price"] or previous_row["price"])

        if current_price >= previous_price:
            continue

        drop_amount = previous_price - current_price
        drop_pct = (drop_amount / previous_price) * 100

        # Find users watching this product
        watchers = (
            supabase.table("watchlist")
            .select("user_id,target_price,id")
            .eq("product_id", product_id)
            .execute()
        )

        for watcher in watchers.data:
            user_id = watcher["user_id"]
            target_price = watcher.get("target_price")

            should_alert = drop_pct >= DROP_THRESHOLD_PCT
            if target_price and current_price <= float(target_price):
                should_alert = True

            if should_alert:
                user_alerts[user_id].append({
                    "name": product["name"],
                    "url": product["url"],
                    "old_price": previous_price,
                    "new_price": current_price,
                    "drop_pct": drop_pct,
                    "target_price": target_price,
                })

    if not user_alerts:
        print("[detect_drops] No price drops to alert.")
        return

    # Fetch user emails from auth.users via service role
    user_ids = list(user_alerts.keys())
    sent = 0
    errors = 0

    for user_id in user_ids:
        try:
            user_resp = supabase.auth.admin.get_user_by_id(user_id)
            email = user_resp.user.email if user_resp.user else None
            if not email:
                continue

            alerts = user_alerts[user_id]
            subject = f"Price drop alert: {len(alerts)} shoe{'s' if len(alerts) > 1 else ''} on your watchlist"
            body_lines = [
                "Good news! The following shoes on your GTA Running Deals watchlist have dropped in price:\n"
            ]

            for alert in alerts:
                target_note = ""
                if alert["target_price"] and alert["new_price"] <= alert["target_price"]:
                    target_note = f" (hit your target of {format_price(alert['target_price'])})"
                body_lines.append(
                    f"  {alert['name']}\n"
                    f"  Was: {format_price(alert['old_price'])}  Now: {format_price(alert['new_price'])}"
                    f"  ({format_pct(alert['drop_pct'])} off){target_note}\n"
                    f"  {alert['url']}\n"
                )

            body_lines.append(
                "\nView all your deals at https://gtarunningdeals.ca/watchlist\n\n"
                "To unsubscribe from these alerts, remove the shoe from your watchlist."
            )

            resend.Emails.send({
                "from": FROM_EMAIL,
                "to": email,
                "subject": subject,
                "text": "\n".join(body_lines),
            })
            sent += 1

        except Exception as e:
            print(f"[detect_drops] Failed to send alert for user {user_id}: {e}")
            errors += 1

    print(f"[detect_drops] Sent {sent} alert emails. {errors} errors.")

    if errors > 0:
        send_developer_alert(
            f"detect_drops: {errors} alert email failures",
            f"{errors} emails failed to send out of {len(user_ids)} users.",
        )


if __name__ == "__main__":
    main()
