from datetime import datetime, timedelta
from crawler import FdaCrawler
from notifier import EmailNotifier

import os
import json
import sys

STATE_FILE = "last_ids.json"
LOOKBACK_DAYS = 3


def get_last_ids():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading state file: {e}")
    return {}


def save_last_ids(ids_dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ids_dict, f, indent=4)


def main():
    print(f"Starting FDA Press Announcements Monitor (last {LOOKBACK_DAYS} days)...")

    crawler = FdaCrawler()
    notifier = EmailNotifier()
    last_ids = get_last_ids()

    posts = crawler.fetch_posts()

    if posts is None:
        print("CRITICAL: Failed to fetch FDA posts.")
        success = notifier.send_notification([], fda_error=True)
        if not success:
            sys.exit(1)
        return

    # Filter posts within the lookback window
    cutoff = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).date()
    new_posts = [p for p in posts if p["date"] >= cutoff]

    # Update state with the newest post id
    if posts:
        last_ids["fda"] = posts[0]["id"]

    for post in new_posts:
        print(f"- [{post['source']}] {post['date']} | {post['title']}")
        print(f"  {post['url']}")

    print(f"Found {len(new_posts)} post(s) within the last {LOOKBACK_DAYS} days.")

    success = notifier.send_notification(new_posts)
    if not success:
        print("CRITICAL: Notification failed to send.")
        sys.exit(1)

    save_last_ids(last_ids)
    print("Process completed successfully.")


if __name__ == "__main__":
    main()
