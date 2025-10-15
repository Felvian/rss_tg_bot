import aiohttp, aiofiles, os, uuid
from typing import Optional

TMP = '/tmp/rss_media'
os.makedirs(TMP, exist_ok=True)

async def download_file(url: str) -> Optional[str]:
    ext = url.split('?')[0].split('.')[-1][:4]
    path = os.path.join(TMP, f"{uuid.uuid4()}.{ext}")
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                return None
            async with aiofiles.open(path, 'wb') as f:
                async for chunk in resp.content.iter_chunked(1024):
                    await f.write(chunk)
    return path

def delete_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass