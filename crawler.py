import requests
from bs4 import BeautifulSoup
import re

class KofairCrawler:
    BASE_URL = "https://www.kofair.or.kr"
    LIST_URL = f"{BASE_URL}/home/board/brdList.do?menu_cd=000064"
    DETAIL_URL_TEMPLATE = f"{BASE_URL}/home/board/brdDetail.do?menu_cd=000064&num={{}}"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_posts(self):
        """
        Fetches the list of posts from the board (JSON response).
        Returns a list of dictionaries containing post info.
        """
        try:
            response = requests.get(self.LIST_URL, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            board_list = data.get("brdList", [])
            
            posts = []
            for item in board_list:
                post_num = str(item.get("num"))
                title = item.get("title", "")
                date = item.get("write_dt", "")
                
                posts.append({
                    "id": post_num,
                    "title": title,
                    "date": date,
                    "url": self.DETAIL_URL_TEMPLATE.format(post_num),
                    "is_notice": False # JSON doesn't explicitly mark notice, but fstBrdList does
                })
            
            # Handle notices if needed from fstBrdList
            fst_list = data.get("fstBrdList", [])
            notice_ids = [str(i.get("num")) for i in fst_list]
            for post in posts:
                if post["id"] in notice_ids:
                    post["is_notice"] = True

            return posts
        except Exception as e:
            print(f"Error fetching posts: {e}")
            return []

if __name__ == "__main__":
    crawler = KofairCrawler()
    latest_posts = crawler.fetch_posts()
    for post in latest_posts[:5]:
        print(f"[{post['id']}] {post['title']} ({post['date']}) - {post['url']}")
