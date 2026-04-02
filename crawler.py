import requests
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup


class RssCrawler:
    NAMESPACES = {"content": "http://purl.org/rss/1.0/modules/content/"}

    def __init__(self, url, source_name):
        self.url = url
        self.source_name = source_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_posts(self):
        """
        Fetches press announcements via RSS feed.
        Returns a list of dicts: {id, title, description, date (datetime.date), url, source}
        """
        try:
            session = requests.Session()
            response = session.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()

            content = response.content
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                root = ET.fromstring(content.decode("utf-8", "ignore"))

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

                # Use URL slug or guid as unique ID
                # For GovDelivery, the link often contains the ID
                post_id = url.rstrip("/").split("/")[-1]
                if "=" in post_id:
                    post_id = post_id.split("=")[-1]
                
                # Try to use guid if available
                guid = item.findtext("guid")
                if guid:
                    post_id = guid

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


class ThaiFdaCrawler:
    MONTH_MAP = {
        "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "메.ย.": 4, 
        "메.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
        "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
        # Adding English abbreviations as fallback if they appear
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }

    def __init__(self, url="https://en.fda.moph.go.th/news/", source_name="TH_FDA"):
        self.url = url
        self.source_name = source_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_posts(self):
        """
        Fetches news from Thailand FDA English page.
        Returns a list of dicts: {id, title, description, date (datetime.date), url, source}
        """
        try:
            session = requests.Session()
            response = session.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            
            items = []
            for h3 in soup.find_all('h3'):
                a_parent = h3.find_parent('a')
                if a_parent and "/news/" in a_parent.get('href', ''):
                    items.append(a_parent)

            posts = []
            for item in items:
                title_elem = item.find('h3')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = item['href']
                if not url.startswith('http'):
                    url = "https://en.fda.moph.go.th" + url

                date_elem = None
                for div in item.find_all('div'):
                    text = div.get_text()
                    if "Publish Date" in text:
                        date_elem = div
                        break
                
                post_date = None
                if date_elem:
                    date_text = date_elem.get_text(strip=True).replace("Publish Date", "").strip()
                    match = re.search(r'(\d{1,2})\s+([^\s]+)\s+(\d{2})', date_text)
                    if match:
                        day = match.group(1)
                        month_abbr = match.group(2)
                        year_be = match.group(3)
                        post_date = self._parse_thai_date(f"{day} {month_abbr} {year_be}")
                
                if not title or not url or not post_date:
                    continue

                post_id = url.rstrip("/").split("/")[-1]

                posts.append({
                    "id": post_id,
                    "title": title,
                    "description": "",
                    "date": post_date,
                    "url": url,
                    "source": self.source_name,
                })

            return posts

        except Exception as e:
            print(f"Error fetching {self.source_name} crawler: {e}")
            return None

    def _parse_thai_date(self, date_str):
        """Parses Thai date format e.g., "12 มี.ค. 69"."""
        try:
            parts = date_str.split()
            if len(parts) < 3:
                return None
            
            day = int(parts[0])
            month_abbr = parts[1]
            year_be_short = int(parts[2])
            
            month = self.MONTH_MAP.get(month_abbr)
            if not month:
                return None
            
            year_ce = (2500 + year_be_short) - 543
            return datetime(year_ce, month, day).date()
        except Exception:
            return None


if __name__ == "__main__":
    # Test FDA (using GovDelivery RSS)
    fda_crawler = RssCrawler("https://public.govdelivery.com/accounts/USFDA/feed.rss", "FDA")
    fda_posts = fda_crawler.fetch_posts()
    if fda_posts:
        print(f"FDA (GovDelivery) posts fetched: {len(fda_posts)}")
        for post in fda_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")

    # Test MFDS
    mfds_crawler = RssCrawler("http://www.mfds.go.kr/www/rss/brd.do?brdId=ntc0004", "MFDS")
    mfds_posts = mfds_crawler.fetch_posts()
    if mfds_posts:
        print(f"\nMFDS posts fetched: {len(mfds_posts)}")
        for post in mfds_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")

    # Test EFSA
    efsa_crawler = RssCrawler("https://www.efsa.europa.eu/en/publications/rss", "EFSA")
    efsa_posts = efsa_crawler.fetch_posts()
    if efsa_posts:
        print(f"\nEFSA posts fetched: {len(efsa_posts)}")
        for post in efsa_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")

    # Test FSA
    fsa_crawler = RssCrawler("https://www.food.gov.uk/rss-feed/news", "FSA")
    fsa_posts = fsa_crawler.fetch_posts()
    if fsa_posts:
        print(f"\nFSA posts fetched: {len(fsa_posts)}")
        for post in fsa_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")

    # Test Thai FDA
    th_crawler = ThaiFdaCrawler()
    th_posts = th_crawler.fetch_posts()
    if th_posts:
        print(f"\nThai FDA posts fetched: {len(th_posts)}")
        for post in th_posts[:3]:
            print(f"  [{post['date']}] {post['title']}")
