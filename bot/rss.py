import feedparser, re
from typing import List, Dict

def clean_html(raw: str) -> str:
    return re.sub(r'<.*?>', '', raw)

def extract_media(content: str) -> List[str]:
    urls = []
    urls += re.findall(r'<img[^>]+src="([^">]+)"', content)
    urls += re.findall(r'<video[^>]+src="([^">]+)"', content)
    return urls

def get_new_posts(feed_url: str, last_id: str) -> List[Dict]:
    feed = feedparser.parse(feed_url)
    posts = []
    for entry in reversed(feed.entries):
        if entry.id == last_id:
            break
        posts.append({
            'title': entry.title,
            'content': clean_html(entry.content_html)[:500] + '…',
            'url': entry.id,
            'media': extract_media(entry.content_html)
        })
    return posts