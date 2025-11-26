import feedparser, re
from typing import List, Dict

IMG_RE = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.I)
VIDEO_RE = re.compile(r'<video[^>]+src=["\'](.*?)["\']', re.I)
SOURCE_RE = re.compile(r'<source[^>]+src=["\'](.*?\.)mp4["\']', re.I)

def clean_html(raw: str) -> str:
    # Удаляем HTML-теги
    text = re.sub(r'<.*?>', '', raw)
    # Заменяем остатки HTML-сущностей на нормальные символы
    text = re.sub(r'&nbsp;|\xa0', ' ', text)
    # Нормализуем пробелы
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_telegram_stub_and_leading_english(text: str) -> str:
    # Гибкое удаление Telegram-заглушки (с любыми пробелами и регистром)
    # Ищем начало строки с возможными пробелами → фразу → любые пробелы → эмодзи или русский текст
    telegram_pattern = re.compile(
        r'^\s*Please open Telegram to view this post\s+VIEW IN TELEGRAM\s*',
        re.IGNORECASE | re.UNICODE
    )
    text = telegram_pattern.sub('', text)

    # Теперь ищем первый русский символ и обрезаем до него
    ru_match = re.search(r'[а-яА-ЯёЁ]', text)
    if ru_match:
        return text[ru_match.start():]
    return text  # если русского нет — оставляем как есть

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

        # Очищаем HTML и нормализуем пробелы
        clean_text = clean_html(content)

        # Удаляем Telegram-заглушку и английский префикс
        clean_text = remove_telegram_stub_and_leading_english(clean_text)

        posts.append({
            'title': entry.title,
            'content': clean_text[:500] + ('…' if len(clean_text) > 500 else ''),
            'url': getattr(entry, 'link', entry_id_clean),
            'media': extract_media(content)  # исходный content с HTML — для извлечения медиа
        })

    return posts