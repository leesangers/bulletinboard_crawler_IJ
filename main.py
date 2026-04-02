from datetime import datetime, timedelta, timezone
from crawler import RssCrawler, ThaiFdaCrawler
from notifier import EmailNotifier

import os
import json
import sys

STATE_FILE = "last_ids.json"

def get_kst_now():
    # KST is UTC+9
    return datetime.now(timezone(timedelta(hours=9)))

def get_lookback_days():
    """
    Weekday (Mon-Fri) -> 1 (Total 2 days: Today + Yesterday)
    Weekend (Sat-Sun) -> 2 (Total 3 days: Today + 2 days ago)
    """
    now_kst = get_kst_now()
    weekday = now_kst.weekday()
    # 0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat, 6: Sun
    if weekday >= 5:  # Saturday or Sunday
        return 2
    return 1

LOOKBACK_DAYS = get_lookback_days()

# Source URLs
# US FDA is using a GovDelivery RSS feed to avoid bot-protection on the main site.
FDA_RSS_URL = "https://public.govdelivery.com/accounts/USFDA/feed.rss"
MFDS_RSS_URL = "http://www.mfds.go.kr/www/rss/brd.do?brdId=ntc0004"
EFSA_RSS_URL = "https://www.efsa.europa.eu/en/publications/rss"
FSA_RSS_URL = "https://www.food.gov.uk/rss-feed/news"


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
    now_kst = get_kst_now()
    print(f"Starting Press Announcements Monitor (KST: {now_kst.strftime('%Y-%m-%d %H:%M:%S')}, last {LOOKBACK_DAYS+1} days)...")

    # Instantiate crawlers
    crawlers = [
        RssCrawler(FDA_RSS_URL, "FDA"),
        RssCrawler(MFDS_RSS_URL, "MFDS"),
        RssCrawler(EFSA_RSS_URL, "EFSA"),
        RssCrawler(FSA_RSS_URL, "FSA"),
        ThaiFdaCrawler() # Named TH_FDA by default
    ]

    notifier = EmailNotifier()
    last_ids = get_last_ids()

    all_fetched_posts = []
    any_error = False

    for crawler in crawlers:
        posts = crawler.fetch_posts()
        if posts is None:
            print(f"ERROR: Failed to fetch posts from {crawler.source_name}")
            any_error = True
        else:
            all_fetched_posts.extend(posts)
            # Update state with the newest post id for this source
            if posts:
                key = crawler.source_name.lower()
                last_ids[key] = posts[0]["id"]

    if not all_fetched_posts and any_error:
        print("CRITICAL: Failed to fetch posts from all sources.")
        success = notifier.send_notification([], fda_error=True)
        if not success:
            sys.exit(1)
        return

    # Filter posts within the lookback window
    cutoff = (now_kst - timedelta(days=LOOKBACK_DAYS)).date()
    new_posts = [p for p in all_fetched_posts if p["date"] >= cutoff]

    # Sort by date descending
    new_posts.sort(key=lambda x: (x["date"], x["title"]), reverse=True)

    for post in new_posts:
        print(f"- [{post['source']}] {post['date']} | {post['title']}")
        print(f"  {post['url']}")

    print(f"Found {len(new_posts)} total post(s) within the last {LOOKBACK_DAYS} days.")

    success = notifier.send_notification(new_posts)
    if not success:
        print("CRITICAL: Notification failed to send (credentials missing?).")

    save_last_ids(last_ids)
    print("Process completed successfully.")


if __name__ == "__main__":
    main()
