import feedparser, re
from typing import List, Dict

IMG_RE = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.I)
VIDEO_RE = re.compile(r'<video[^>]+src=["\'](.*?)["\']', re.I)
# для тега <source src="…mp4"> внутри <video>
SOURCE_RE = re.compile(r'<source[^>]+src=["\'](.*?\.)mp4["\']', re.I)

def clean_html(raw: str) -> str:
    return re.sub(r'<.*?>', '', raw)

def extract_media(content: str) -> List[str]:
    """Вернуть список прямых URL картинок и видео."""
    urls = []
    urls.extend(IMG_RE.findall(content))
    urls.extend(VIDEO_RE.findall(content))
    urls.extend(SOURCE_RE.findall(content))
    # убираем дубликаты, сохраняя порядок
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def get_new_posts(feed_url: str, last_id: str) -> List[Dict]:
    feed = feedparser.parse(feed_url)
    posts = []
    found_last = False
    last_id_clean = last_id.strip() if last_id else None

    # Идём от новых к старым (как в ленте)
    for entry in feed.entries:
        if last_id_clean and entry_id_clean == last_id_clean:
            break  # достигли последнего отправленного — остальное не нужно
        # Извлекаем данные
        content_raw = entry.get('content', entry.get('summary', ''))
        if isinstance(content_raw, list) and content_raw:
            content = content_raw[0].get('value', '')
        else:
            content = content_raw
        posts.append({
            'title': entry.title,
            'content': clean_html(content)[:500] + '…',
            'url': entry_id_clean,
            'media': extract_media(content)
        })
    # Теперь posts = [новый, ..., последний_новый_после_last_id]
    return posts