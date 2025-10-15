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
from test_cron import start as start_test_cron

log = get_logger("cron")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

LAST_FILE = '/app/data/last_ids.json'

async def periodic_job():
    while True:
        try:
            log.info("Запуск проверки RSS-лент...")
            for fid, username in list_feeds().items():
                url = build_url(username)
                last_id = get_last_id(url)
                posts = get_new_posts(url, last_id)  # уже в правильном порядке: новые первыми
                for post in posts:
                    await send_post(post)
                    await asyncio.sleep(1.2)
                if posts:
                    save_last_id(url, posts[0]['url'])  # самый свежий — первый в списке
            log.info("Проверка завершена.")
        except Exception as e:
            log.exception("Ошибка в периодической задаче: %s", e)
        # Ждём 5 минут = 300 секунд
        await asyncio.sleep(300)

def get_last_id(url: str) -> str | None:
    try:
        raw = json.load(open(LAST_FILE)).get(url)
        return raw.strip() if raw else None
    except Exception:
        return None

def save_last_id(url: str, post_id: str):
    data = json.load(open(LAST_FILE)) if os.path.exists(LAST_FILE) else {}
    data[url] = post_id.strip()
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
        last = posts[0]                      # самый свежий
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
    asyncio.create_task(periodic_job())

    log.info("Бот запущен. Фоновая задача RSS активна.")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        log.info("Остановка бота...")

if __name__ == '__main__':
    asyncio.run(main())