import logging
import logging.config
import asyncio
# Patch asyncio.coroutine for motor under Python 3.11+
if not hasattr(asyncio, "coroutine"):
    import types
    asyncio.coroutine = lambda f: f

import os
import sys
import re
from datetime import datetime, timedelta

try:
    import tgcrypto
except ImportError:
    pass
from pyrogram import Client, __version__, types, idle
from pyrogram.raw.all import layer
from typing import Union, Optional, AsyncGenerator

# Database modules (Updated for 5 DBs)
from database.ia_filterdb import Media, Media2, Media3, Media4, Media5, choose_mediaDB, db as clientDB
from database.users_chats_db import db

# Info imports
from info import (
    SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, 
    DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5,
    RESTART_INTERVAL, URL
)
from utils import temp
from sample_info import tempDict

# Webserver and Indexing imports
from aiohttp import web as webserver, ClientSession, ClientTimeout
from plugins.webcode import bot_run
# Ensure you import your merged indexing function and incol here:
from plugins.index import index_files_to_db_all, incol 

from os import environ

# Prevent asyncio logging spam
logging.getLogger("asyncio").setLevel(logging.CRITICAL - 1)

# Peer ID invalid fix (Crucial for certain forwarded messages)
from pyrogram import utils as pyroutils
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

# Load logging config
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

PORT_CODE = environ.get("PORT", "8080")

async def restart_index(bot):
    """Resumes interrupted indexing tasks using MongoDB progress."""
    progress_document = incol.find_one({"_id": "index_progress"})
    if progress_document:
        last_indexed_file = progress_document.get("last_indexed_file", 0)
        last_msg_id = progress_document.get("last_msg_id")
        chat_id = progress_document.get("chat_id")            
        temp.CURRENT = int(last_indexed_file)
        
        msg = await bot.send_message(chat_id=int(LOG_CHANNEL), text="🔄 Restarting interrupted Indexing process...")
        logging.info(f"Resuming index at message {temp.CURRENT}")
        
        # Resuming using the round-robin indexer
        await index_files_to_db_all(last_msg_id, chat_id, msg, bot)                    

async def keep_alive():
    """
    Pings the bot's own  URL every 10 minutes to prevent it from sleeping.
    Set the URL environment variable to your Render app URL.
    e.g. https://your-app-name.onrender.com
    """
    if not URL:
        logging.info("URL not set — keep-alive ping disabled.")
        return

    url = URL.rstrip("/")
    timeout = ClientTimeout(total=30)
    logging.info(f"Keep-alive started → pinging {url} every 10 minutes.")

    while True:
        await asyncio.sleep(3 * 60)  # wait 3 minutes between pings
        try:
            async with ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    logging.info(f"Keep-alive ping → {resp.status}")
        except Exception as e:
            logging.warning(f"Keep-alive ping failed: {e}")


class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        # Load banned users/chats
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        await super().start()

        # Ensure indexes in all 5 DBs safely
        await Media.ensure_indexes()
        if DATABASE_URI2: await Media2.ensure_indexes()
        if DATABASE_URI3: await Media3.ensure_indexes()
        if DATABASE_URI4: await Media4.ensure_indexes()
        if DATABASE_URI5: await Media5.ensure_indexes()

        # Initialize dynamic DB routing
        await choose_mediaDB()

        # Get bot info
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = "@" + me.username
        logging.info(f"{me.first_name} (Pyrogram v{__version__}, Layer {layer}) started on @{me.username}.")

        # Log channel message
        try:
            await self.send_message(
                chat_id=LOG_CHANNEL,
                text="✅ Bot Started Successfully!\n⚡ 5-DB Feature & Auto-Restart Active."
            )
        except Exception as e:
            logging.error(f"Could not send start message: {e}")

        print("⚡ Og Eva Re-edited — 5 DB System Initialized ⚡")

        # Run web server
        client = webserver.AppRunner(await bot_run())
        await client.setup()
        bind_address = "0.0.0.0"
        await webserver.TCPSite(client, bind_address, PORT_CODE).start()

        # Check for interrupted indexing tasks
        await restart_index(self)

        # Schedule restart
        asyncio.create_task(self.schedule_restart(RESTART_INTERVAL))

        # Keep Render awake with a self-ping every 10 minutes
        asyncio.create_task(keep_alive())

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye 👋")

    async def restart(self):
        logging.info("Restarting bot process...")
        await self.stop()
        # VPS/Koyeb/Docker/Render compatible restart
        os._exit(0)

    async def schedule_restart(self, interval: str = RESTART_INTERVAL):
        """
        Automatically restart the bot after the given interval.
        Example interval: '12h', '1d', '30m'
        """
        if not interval:
            logging.warning("No restart interval set — skipping auto-restart.")
            return

        try:
            seconds = parse_interval(interval)
        except Exception as e:
            logging.error(f"Invalid restart interval '{interval}': {e}")
            return

        while True:
            try:
                # Sleep until 1 minute before restart
                await asyncio.sleep(max(0, seconds - 60))
                try:
                    await self.send_message(
                        chat_id=LOG_CHANNEL,
                        text=f"⚠️ Bot will restart in 1 minute (Scheduled every {interval}) to clear memory.",
                    )
                except Exception as e:
                    logging.error(f"Could not send restart warning: {e}")

                await asyncio.sleep(60)
                await self.restart()
            except Exception as e:
                logging.error(f"Restart loop error: {e}")
                await asyncio.sleep(60)

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """
        Custom message iterator that fetches messages in chunks.
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(
                chat_id, list(range(current, current + new_diff + 1))
            )
            for message in messages:
                yield message
                current += 1

# Helper function: Parse restart interval
def parse_interval(interval: str) -> int:
    """
    Convert interval string like '1h', '2d', '30m' to seconds.
    """
    match = re.match(r"(\d+)([dhm])", interval.lower())
    if not match:
        raise ValueError("Invalid interval format. Use e.g., '1h', '2d', '30m'.")
    value, unit = match.groups()
    value = int(value)
    if unit == "d": return value * 24 * 60 * 60
    elif unit == "h": return value * 60 * 60
    elif unit == "m": return value * 60
    else: raise ValueError("Invalid time unit. Only 'd', 'h', 'm' are allowed.")


if __name__ == "__main__":
    app = Bot()
    app.run()
