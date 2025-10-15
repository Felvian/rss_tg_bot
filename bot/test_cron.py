import asyncio, logging, traceback
from aiocron import crontab
from datetime import datetime

log = logging.getLogger("tcron")
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(message)s"))
log.addHandler(handler)

async def tick():
    log.info("TICK %s", datetime.now())

@crontab("* * * * * */10", start=False)   # каждые 10 секунд
async def every_10s():
    try:
        await tick()
    except Exception as exc:
        log.error("cron failed: %s\n%s", exc, traceback.format_exc())

def start():
    every_10s.start()
    log.info("test-cron started")