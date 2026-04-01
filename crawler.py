import requests
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re


class RssCrawler:
    NAMESPACES = {"content": "http://purl.org/rss/1.0/modules/content/"}

    def __init__(self, url, source_name):
        self.url = url
        self.source_name = source_name
        self.headers = {"User-Agent": "curl/7.88.1"}

    def fetch_posts(self):
        """
        Fetches press announcements via RSS feed.
        Returns a list of dicts: {id, title, description, date (datetime.date), url, source}
        """
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                print(f"No <channel> found in RSS feed for {self.source_name}.")
                return []

            posts = []
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                url = (item.findtext("link") or "").strip()
                
                # Check for description first, then content:encoded
                description = (item.findtext("description") or "").strip()
                if not description:
                    content_encoded = item.find("content:encoded", self.NAMESPACES)
                    if content_encoded is not None:
                        description = (content_encoded.text or "").strip()

                pub_date_str = (item.findtext("pubDate") or "").strip()

                if not title or not url:
                    continue

                post_date = self._parse_date(pub_date_str)
                if post_date is None:
                    continue

                # Use URL slug as unique ID
                post_id = url.rstrip("/").split("/")[-1]
                if "=" in post_id:
                    post_id = post_id.split("=")[-1]

                posts.append({
                    "id": post_id,
                    "title": title,
                    "description": description,
                    "date": post_date,
                    "url": url,
                    "source": self.source_name,
                })

            return posts

        except Exception as e:
            print(f"Error fetching {self.source_name} RSS feed: {e}")
            return None

    def _parse_date(self, date_str):
        """Parse RFC 2822 date string to datetime.date."""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.date()
        except Exception:
            return None


if __name__ == "__main__":
    # Test FDA
    fda_crawler = RssCrawler("https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml", "FDA")
    fda_posts = fda_crawler.fetch_posts()
    if fda_posts:
        print(f"FDA posts fetched: {len(fda_posts)}")
        for post in fda_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")

    # Test MFDS
    mfds_crawler = RssCrawler("http://www.mfds.go.kr/www/rss/brd.do?brdId=ntc0004", "MFDS")
    mfds_posts = mfds_crawler.fetch_posts()
    if mfds_posts:
        print(f"\nMFDS posts fetched: {len(mfds_posts)}")
        for post in mfds_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")
