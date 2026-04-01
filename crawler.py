import requests
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re


class FdaCrawler:
    RSS_URL = "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"

    def __init__(self):
        self.headers = {"User-Agent": "curl/7.88.1"}

    def fetch_posts(self):
        """
        Fetches FDA press announcements via RSS feed.
        Returns a list of dicts: {id, title, description, date (datetime.date), url, source}
        """
        try:
            response = requests.get(self.RSS_URL, headers=self.headers, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                print("No <channel> found in RSS feed.")
                return []

            posts = []
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                url = (item.findtext("link") or "").strip()
                description = (item.findtext("description") or "").strip()
                pub_date_str = (item.findtext("pubDate") or "").strip()

                if not title or not url:
                    continue

                post_date = self._parse_date(pub_date_str)
                if post_date is None:
                    continue

                # Use URL slug as unique ID
                post_id = url.rstrip("/").split("/")[-1]

                posts.append({
                    "id": post_id,
                    "title": title,
                    "description": description,
                    "date": post_date,
                    "url": url,
                    "source": "FDA",
                })

            return posts

        except Exception as e:
            print(f"Error fetching FDA RSS feed: {e}")
            return None

    def _parse_date(self, date_str):
        """Parse RFC 2822 date string (e.g. 'Thu, 26 Mar 2026 18:47:15 EDT') to datetime.date."""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.date()
        except Exception:
            return None


if __name__ == "__main__":
    crawler = FdaCrawler()
    posts = crawler.fetch_posts()
    if posts:
        print(f"Total posts fetched: {len(posts)}")
        for post in posts[:5]:
            print(f"\n[{post['source']}] {post['date']}")
            print(f"  {post['title']}")
            print(f"  {post['url']}")
    else:
        print("No posts found or error occurred.")
