import feedparser, re
from typing import List, Dict

IMG_RE = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.I)
VIDEO_RE = re.compile(r'<video[^>]+src=["\'](.*?)["\']', re.I)
SOURCE_RE = re.compile(r'<source[^>]+src=["\'](.*?\.)mp4["\']', re.I)

# Убираем типичные Telegram-заглушки в начале
TELEGRAM_STUB_RE = re.compile(
    r'^\s*Please open Telegram to view this post\s+VIEW IN TELEGRAM\s*',
    re.IGNORECASE | re.MULTILINE
)

RU_START = re.compile(r'[а-яА-ЯёЁ]')

def clean_html(raw: str) -> str:
    return re.sub(r'<.*?>', '', raw)

def remove_leading_noise(text: str) -> str:
    # Шаг 1: Удалить Telegram-заглушку
    text = TELEGRAM_STUB_RE.sub('', text)
    
    # Шаг 2: Найти первый русский символ и обрезать до него
    match = RU_START.search(text)
    if match:
        return text[match.start():]
    return text.strip()  # если русского нет — вернём как есть, но без пробелов

def extract_media(content: str) -> List[str]:
    urls = []
    urls.extend(IMG_RE.findall(content))
    urls.extend(VIDEO_RE.findall(content))
    urls.extend(SOURCE_RE.findall(content))
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def get_new_posts(feed_url: str, last_id: str) -> List[Dict]:
    feed = feedparser.parse(feed_url)
    posts = []
    last_id_clean = last_id.strip() if last_id else None

    for entry in feed.entries:
        entry_id_clean = entry.id.strip()
        if last_id_clean and entry_id_clean == last_id_clean:
            break

        content_raw = entry.get('content', entry.get('summary', ''))
        if isinstance(content_raw, list) and content_raw:
            content = content_raw[0].get('value', '')
        else:
            content = content_raw

        clean_text = clean_html(content)
        clean_text = remove_leading_noise(clean_text)

        posts.append({
            'title': entry.title,
            'content': clean_text[:500] + ('…' if len(clean_text) > 500 else ''),
            'url': getattr(entry, 'link', entry_id_clean),
            'media': extract_media(content)
        })

    return posts