import json, uuid, os

FEEDS_FILE = '/app/data/feeds.json'

def load_feeds():
    if not os.path.exists(FEEDS_FILE):
        return {}
    with open(FEEDS_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_feeds(feeds):
    os.makedirs(os.path.dirname(FEEDS_FILE), exist_ok=True)
    with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=2)

def add_feed(username: str) -> str:
    feeds = load_feeds()
    fid = str(uuid.uuid4())[:8]
    feeds[fid] = username
    save_feeds(feeds)
    return fid

def remove_feed(fid: str) -> bool:
    feeds = load_feeds()
    if fid in feeds:
        del feeds[fid]
        save_feeds(feeds)
        return True
    return False

def list_feeds():
    return load_feeds()