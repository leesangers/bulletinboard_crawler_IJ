from datetime import datetime, timedelta
from crawler import RssCrawler
from notifier import EmailNotifier

import os
import json
import sys

STATE_FILE = "last_ids.json"
LOOKBACK_DAYS = 10

FDA_RSS_URL = "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"
MFDS_RSS_URL = "http://www.mfds.go.kr/www/rss/brd.do?brdId=ntc0004"


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
    print(f"Starting Press Announcements Monitor (last {LOOKBACK_DAYS} days)...")

    fda_crawler = RssCrawler(FDA_RSS_URL, "FDA")
    mfds_crawler = RssCrawler(MFDS_RSS_URL, "MFDS")
    notifier = EmailNotifier()
    last_ids = get_last_ids()

    fda_posts = fda_crawler.fetch_posts()
    mfds_posts = mfds_crawler.fetch_posts()

    if fda_posts is None and mfds_posts is None:
        print("CRITICAL: Failed to fetch both FDA and MFDS posts.")
        success = notifier.send_notification([], fda_error=True)
        if not success:
            sys.exit(1)
        return

    all_posts = (fda_posts or []) + (mfds_posts or [])

    # Filter posts within the lookback window
    cutoff = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).date()
    new_posts = [p for p in all_posts if p["date"] >= cutoff]

    # Sort by date descending
    new_posts.sort(key=lambda x: x["date"], reverse=True)

    # Update state with the newest post ids
    if fda_posts:
        last_ids["fda"] = fda_posts[0]["id"]
    if mfds_posts:
        last_ids["mfds"] = mfds_posts[0]["id"]

    for post in new_posts:
        print(f"- [{post['source']}] {post['date']} | {post['title']}")
        print(f"  {post['url']}")

    print(f"Found {len(new_posts)} total post(s) within the last {LOOKBACK_DAYS} days.")

    success = notifier.send_notification(new_posts)
    if not success:
        print("CRITICAL: Notification failed to send.")
        sys.exit(1)

    save_last_ids(last_ids)
    print("Process completed successfully.")


if __name__ == "__main__":
    main()
