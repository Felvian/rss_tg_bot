import os
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_ID  = os.getenv("CHANNEL_ID")
BRIDGE_URL  = 'http://rss-bridge/?action=display&bridge=TelegramBridge&username={username}&_cache_timeout=300&format=Atom'