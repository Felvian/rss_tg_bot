import aiohttp
import aiofiles
import os
import uuid
from typing import Optional
from urllib.parse import urlparse
import posixpath

TMP = '/tmp/rss_media'
os.makedirs(TMP, exist_ok=True)

def get_safe_extension(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    ext = posixpath.splitext(path)[1].lstrip('.').lower()
    # Ограничиваем только разрешёнными расширениями
    if ext in {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mov', 'avi', 'mkv'}:
        return ext
    return 'bin'  # или 'jpg', если хотите по умолчанию как изображение

async def download_file(url: str) -> Optional[str]:
    ext = get_safe_extension(url)
    path = os.path.join(TMP, f"{uuid.uuid4()}.{ext}")
    
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.get(url) as resp:
                if resp.status != 200:
                    return None
                async with aiofiles.open(path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(1024):
                        await f.write(chunk)
            return path
        except Exception:
            # При ошибке не оставляем битый файл
            if os.path.exists(path):
                os.remove(path)
            raise

def delete_file(path: str):
    try:
        os.remove(path)
    except (OSError, FileNotFoundError):
        pass