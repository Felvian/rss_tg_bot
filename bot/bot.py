import asyncio, json, os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, FSInputFile
from aiocron import crontab

from config import BOT_TOKEN, CHANNEL_ID, BRIDGE_URL
from db import add_feed, remove_feed, list_feeds
from rss import get_new_posts
from download import download_file, delete_file
from logger import get_logger   # если модуль лежит рядом

log = get_logger("cron")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

LAST_FILE = '/app/data/last_ids.json'

def get_last_id(url: str) -> str | None:
    try:
        return json.load(open(LAST_FILE)).get(url)
    except Exception:
        return None

def save_last_id(url: str, post_id: str):
    data = json.load(open(LAST_FILE)) if os.path.exists(LAST_FILE) else {}
    data[url] = post_id
    os.makedirs(os.path.dirname(LAST_FILE), exist_ok=True)
    json.dump(data, open(LAST_FILE, 'w'))

def build_url(username: str) -> str:
    return BRIDGE_URL.format(username=username)

async def send_post(post: dict):
    text = f"<b>{post['title']}</b>\n\n{post['content']}\n\n<a href='{post['url']}'>Источник</a>"
    media_urls = post['media'][:10]
    if not media_urls:
        await bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
        return

    files = []
    try:
        for idx, url in enumerate(media_urls):
            path = await download_file(url)
            if not path:
                continue
            file = FSInputFile(path)

            # выбираем нужный класс
            if url.endswith(('.mp4', '.webm', '.mov')):
                cls = InputMediaVideo
            elif url.endswith('.gif'):
                cls = InputMediaDocument
            else:
                cls = InputMediaPhoto

            # ПЕРВЫЙ объект несёт caption и parse_mode
            if idx == 0:
                files.append(cls(media=file, caption=text, parse_mode='HTML'))
            else:
                files.append(cls(media=file))   # без caption/parse_mode

        if not files:
            await bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
            return

        await bot.send_media_group(CHANNEL_ID, files)
    finally:
        for f in files:
            delete_file(f.media.path)

@dp.message(Command('start'))
async def start(m: types.Message):
    await m.answer(
        "👋 RSS-бот готов!\n\n"
        "/add <channel>  — добавить канал (без @)\n"
        "/list             — показать добавленные\n"
        "/remove <id>      — удалить канал"
    )

@dp.message(Command('add'))
async def add(m: types.Message):
    args = m.text.split()
    if len(args) != 2:
        await m.answer("❗ Использование: /add channel_name")
        return
    username = args[1].lstrip('@')
    fid = add_feed(username)
    await m.answer(f"✅ Канал `@{username}` добавлен. ID: `{fid}`", parse_mode='Markdown')
    url = build_url(username)
    print(url)
    posts = get_new_posts(url, None)
    print(posts)          # None = берём всю ленту
    if posts:
        last = posts[-1]                      # самый свежий
        await send_post(last)                 # отправляем
        save_last_id(url, last['url'])        # запоминаем, чтобы не повторять
    else:
        await m.answer("📭 В ленте пока нет постов.")

@dp.message(Command('list'))
async def lst(m: types.Message):
    feeds = list_feeds()
    if not feeds:
        await m.answer("📭 Список пуст.")
        return
    txt = "📋 Добавленные каналы:\n\n" + "\n".join([f"`{k}` — @{v}" for k, v in feeds.items()])
    await m.answer(txt, parse_mode='Markdown')

@dp.message(Command('remove'))
async def rm(m: types.Message):
    args = m.text.split()
    if len(args) != 2:
        await m.answer("❗ Использование: /remove <id>")
        return
    ok = remove_feed(args[1])
    await m.answer("✅ Удалено." if ok else "❌ ID не найден.")

@crontab('*/5 * * * *', start=False)   # start=False → сами запустим
async def job():
    log.info("cron job tick")
    for fid, username in list_feeds().items():
        url = build_url(username)
        last_id = get_last_id(url)
        for post in get_new_posts(url, last_id):
            await send_post(post)          # теперь await
            save_last_id(url, post['url'])

async def main():
    job.start()
    log.info("bot started, cron active")
    try:
        await dp.start_polling(bot)
    finally:
        job.stop()    
    

if __name__ == '__main__':
    asyncio.run(main())