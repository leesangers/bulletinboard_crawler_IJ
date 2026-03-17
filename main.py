import os
import json
from crawler import KofairCrawler
from notifier import EmailNotifier

STATE_FILE = "last_id.txt"

def get_last_id():
    """Reads the last known post ID from a file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_id(last_id):
    """Saves the latest post ID to a file."""
    with open(STATE_FILE, "w") as f:
        f.write(str(last_id))

def main():
    print("Starting KOFAIR Bulletin Board Monitor...")
    
    crawler = KofairCrawler()
    notifier = EmailNotifier()
    
    # 1. Fetch current posts from website
    current_posts = crawler.fetch_posts()
    if not current_posts:
        print("No posts found or error occurred.")
        return

    # 2. Identify new posts
    last_id = get_last_id()
    new_posts = []

    if last_id is None:
        # First run: take the latest 5 posts as 'new' or just set last_id
        print("First run detected. Setting baseline.")
        new_posts = current_posts[:5] # Notify top 5 for initial setup
        if current_posts:
            save_last_id(current_posts[0]["id"])
    else:
        # Find posts with ID > last_id (assuming numeric or chronological order)
        # However, IDs might not be purely numeric. Since we fetch descending, 
        # we stop when we hit last_id.
        for post in current_posts:
            if post["id"] == last_id:
                break
            new_posts.append(post)
        
        # Update last_id to the very latest if new posts exist
        if new_posts:
            save_last_id(current_posts[0]["id"])

    # 3. Notify if there are new posts
    if new_posts:
        print(f"Found {len(new_posts)} new posts.")
        # Filter logic (keywords like CP, 하도급 etc. from PRD)
        keywords = ["CP", "하도급", "교육", "제재", "과징금", "동반성장"]
        for post in new_posts:
            if any(kw in post["title"] for kw in keywords):
                post["title"] = f"★[중점] {post['title']}"
            print(f"- {post['title']} ({post['url']})")
        
        notifier.send_notification(new_posts)
    else:
        print("No new posts found.")

if __name__ == "__main__":
    main()
