import feedparser, re
from typing import List, Dict

IMG_RE = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.I)
VIDEO_RE = re.compile(r'<video[^>]+src=["\'](.*?)["\']', re.I)
# для тега <source src="…mp4"> внутри <video>
SOURCE_RE = re.compile(r'<source[^>]+src=["\'](.*?\.)mp4["\']', re.I)


# Паттерн для поиска первого русского символа или слова
RU_START = re.compile(r'[а-яА-ЯёЁ]')

def clean_html(raw: str) -> str:
    return re.sub(r'<.*?>', '', raw)

def remove_leading_english(text: str) -> str:
    """Удаляет текст до первого русского символа включительно (начало русской части)."""
    match = RU_START.search(text)
    if match:
        return text[match.start():]
    return text  # если русских символов нет — возвращаем как есть

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
        entry_id_clean = entry.id.strip()
        if last_id_clean and entry_id_clean == last_id_clean:
            break  # достигли последнего отправленного — остальное не нужно
        # Извлекаем данные
        content_raw = entry.get('content', entry.get('summary', ''))
        print(content_raw)
        if isinstance(content_raw, list) and content_raw:
            content = content_raw[0].get('value', '')
        else:
            content = content_raw
        clean_text = clean_html(content)
        clean_text = remove_leading_english(clean_text)           
        posts.append({
            'title': entry.title,
            'content':  clean_text[:500] + ('…' if len(clean_text) > 500 else ''),
            'url': entry_id_clean,
            'media': extract_media(content)
        })
    # Теперь posts = [новый, ..., последний_новый_после_last_id]
    return posts
