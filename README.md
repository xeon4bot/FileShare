<h1 align="center">
  ⚡ 5DB Auto Filter Bot
</h1>

<p align="center">
  <b>A high-capacity Telegram Auto Filter Bot with 5-database architecture, batch indexing, parallel duplicate detection, and round-robin file distribution.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python">
  <img src="https://img.shields.io/badge/Pyrogram-2.x-green?style=flat-square">
  <img src="https://img.shields.io/badge/MongoDB-5DB-brightgreen?style=flat-square&logo=mongodb">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square">
</p>

---

## 🗄️ What is 5DB?

Most filter bots use a single MongoDB database, which hits the **512 MB free-tier limit** fast. This bot splits all indexed files across **5 independent MongoDB databases**, giving you up to **2.5 GB of free storage** while keeping search and indexing seamless.

- **5× storage** — each DB holds its own slice of your file library
- **Round-robin distribution** — new files are spread evenly across all 5 DBs automatically
- **Unified search** — all 5 databases are queried and results are interleaved in a single response
- **Parallel duplicate checking** — all 5 DBs are checked simultaneously (not one-by-one)
- **Batch indexing** — fetches 200 Telegram messages per API call instead of one at a time

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗄️ **5-Database Storage** | Files distributed across 5 MongoDB URIs via round-robin |
| ⚡ **Batch Indexing** | Fetches 200 messages per Telegram API call for maximum speed |
| 🔍 **Parallel Duplicate Check** | All 5 DBs checked at the same time using `asyncio.gather` |
| 🎯 **Selective DB Indexing** | Admins can choose to index into DB1, DB2, DB3, DB4, or all 5 |
| 🔎 **Auto Filter** | Automatically filters files from connected channels |
| ✏️ **Manual Filter** | Add custom keyword → file/message filters per group |
| 🎬 **IMDB Integration** | Fetch movie/show details automatically on search |
| 📣 **Broadcast** | Send messages to all bot users at once |
| 🔗 **File Store** | Generate shareable links for single or batch posts |
| 🛡️ **Force Subscribe** | Require users to join up to 2 channels before use |
| 🔤 **Spell Check** | Suggests corrections when no results are found |
| 📊 **Live Index Stats** | Real-time progress display (ETC, saved, duplicates, errors) |
| 🔄 **Auto Restart** | Configurable auto-restart interval (days/hours/minutes) |
| 🚫 **Ban / Unban** | Block users from accessing the bot |
| 🔒 **Content Protection** | Optionally prevent forwarding of sent files |
| 👥 **PM Connection** | Users can connect groups to PM for filter management |
| 💬 **Inline Search** | Search files inline from any chat |

---

## ⚙️ Variables

### 🔴 Required

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Get from [@BotFather](https://t.me/BotFather) |
| `API_ID` | Get from [my.telegram.org](https://my.telegram.org/apps) |
| `API_HASH` | Get from [my.telegram.org](https://my.telegram.org/apps) |
| `CHANNELS` | Username or ID of channels/groups to auto-filter. Separate with space |
| `ADMINS` | User IDs of admins. Separate with space |
| `DATABASE_URI` | MongoDB connection URI — **Primary DB (DB1)** |
| `DATABASE_URI2` | MongoDB connection URI — **DB2** |
| `DATABASE_URI3` | MongoDB connection URI — **DB3** |
| `DATABASE_URI4` | MongoDB connection URI — **DB4** |
| `DATABASE_URI5` | MongoDB connection URI — **DB5** (also used for round-robin indexing) |
| `DATABASE_NAME` | Name of the MongoDB database (same name used across all 5 URIs) |
| `LOG_CHANNEL` | Channel ID for bot activity logs. Bot must be admin there |

> 💡 All 5 `DATABASE_URI` values can be free MongoDB Atlas clusters — each gives 512 MB, totalling **~2.5 GB** of free file storage.

### 🟡 Optional

| Variable | Default | Description |
|---|---|---|
| `COLLECTION_NAME` | `file` | MongoDB collection name for indexed files |
| `PICS` | Built-in set | Telegraph image URLs for the start message (space-separated) |
| `AUTH_CHANNEL` | — | Channel IDs users must join (Force Subscribe). Space-separated |
| `AUTH_GROUPS` | — | Group IDs where the bot is authorised to work |
| `AUTH_USERS` | — | Extra users allowed to use the bot |
| `FORCE_SUB_1` | — | First force-subscribe channel ID |
| `FORCE_SUB_2` | — | Second force-subscribe channel ID |
| `FILE_STORE_CHANNEL` | — | Channel(s) used for file store link generation |
| `INDEX_REQ_CHANNEL` | `LOG_CHANNEL` | Channel where non-admin index requests are sent for approval |
| `SUPPORT_CHAT` | — | Telegram username of your support group |
| `CUSTOM_FILE_CAPTION` | Built-in | Caption template for sent files |
| `BATCH_FILE_CAPTION` | Same as above | Caption template for batch file sends |
| `IMDB_TEMPLATE` | Built-in | Template for IMDB result messages |
| `IMDB` | `False` | Enable IMDB lookup on search (`True`/`False`) |
| `USE_CAPTION_FILTER` | `False` | Also search file captions, not just filenames |
| `SINGLE_BUTTON` | `True` | Show filename and file size in one button |
| `P_TTI_SHOW_OFF` | `True` | Redirect users to PM `/start` instead of sending files in group |
| `SPELL_CHECK_REPLY` | `True` | Suggest alternate spellings when no results found |
| `LONG_IMDB_DESCRIPTION` | `False` | Show full IMDB plot instead of short version |
| `MAX_B_TN` | `5` | Maximum number of file buttons shown per result |
| `MAX_LIST_ELM` | — | Limit length of cast/crew lists in IMDB results |
| `PROTECT_CONTENT` | `False` | Prevent forwarding of files sent by the bot |
| `MELCOW_NEW_USERS` | `True` | Welcome message for new users |
| `PUBLIC_FILE_STORE` | `True` | Allow anyone to use file store links |
| `NO_RESULTS_MSG` | `False` | Send a message when no search results are found |
| `CACHE_TIME` | `300` | Inline query cache time in seconds |
| `RESTART_INTERVAL` | `2d` | Auto-restart interval. Use `2d`, `12h`, `30m` format |

---

## 🚀 Deploy

<details>
<summary><b>🖥️ Deploy on VPS</b></summary>

```bash
git clone https://github.com/YourRepo/5DB
cd 5DB
pip3 install -U -r requirements.txt
# Edit info.py or set environment variables
python3 bot.py
```
</details>

<details>
<summary><b>🐳 Deploy with Docker</b></summary>

```bash
git clone https://github.com/YourRepo/5DB
cd 5DB
# Fill in your variables in docker-compose.yml
docker-compose up -d
```
</details>

<details>
<summary><b>☁️ Deploy to Koyeb</b></summary>

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/YourRepo/5DB&branch=main&name=5DB)

Set all required environment variables in the Koyeb dashboard after clicking Deploy.
</details>

---

## 📋 Commands

### 👤 User Commands
```
/start        — Start the bot
/help         — Get help message
/info         — Get your Telegram user info
/id           — Get Telegram IDs
/imdb         — Search IMDB for a movie or show
```

### 🔧 Group Admin Commands
```
/filter       — Add a manual filter
/filters      — List all manual filters in this chat
/del          — Delete a specific manual filter
/delall       — Delete all manual filters in this chat
/connect      — Connect a group to your PM
/disconnect   — Disconnect from PM
/enable       — Re-enable the bot in a chat
/disable      — Disable the bot in a chat
```

### 🛠️ Bot Admin Commands
```
/logs         — Get recent error logs
/stats        — File counts across all 5 databases
/users        — List all bot users
/chats        — List all chats the bot is in
/index        — Index files from a channel into a chosen DB
/setskip      — Set the message ID to resume indexing from
/deleteall    — Delete all indexed files from a chat
/delete       — Delete a specific file from the index
/broadcast    — Broadcast a message to all users
/ban          — Ban a user
/unban        — Unban a user
/leave        — Make the bot leave a chat
/channel      — List all connected channels
/batch        — Generate a file store link for multiple posts
/link         — Generate a file store link for one post
```

---

## 🗄️ How 5DB Indexing Works

When an admin sends a channel link to the bot, they are presented with these options:

```
[ Index To DB1 ]
[ Index To DB2 ]
[ Index To DB3 ]
[ Index To DB4 ]
[ Index To All DBs (Round Robin) ]
```

**Round Robin mode** distributes files evenly — file 1 → DB1, file 2 → DB2, ... file 6 → DB1, and so on. This keeps all databases balanced.

**Batch fetching** pulls 200 Telegram messages per API call. For a 10,000-message channel this means ~50 API calls instead of 10,000 — dramatically faster indexing.

**Parallel duplicate detection** fires all 5 MongoDB `find_one` queries at the same time. Previously each query waited for the last to finish; now the check takes as long as the single slowest DB response.

---

## 🙏 Credits

- [Pyrogram](https://github.com/pyrogram/pyrogram) — Telegram MTProto library by Dan
- [Mahesh0253](https://github.com/Mahesh0253/Media-Search-bot) — Original Media Search Bot
- [TroJanzHEX](https://github.com/trojanzhex) — Unlimited Filter Bot & AutoFilterBot
- [GouthamSER](https://github.com/GouthamSER) — 2DB base this project evolved from
- All contributors and the open-source community ❤️

---

## ⚠️ Disclaimer

[![GNU AGPL v3](https://www.gnu.org/graphics/agplv3-155x51.png)](https://www.gnu.org/licenses/agpl-3.0.en.html)

Licensed under [GNU AGPL v3.0](LICENSE). Selling this code for money is **strictly prohibited**. Fork freely, credit fairly.
