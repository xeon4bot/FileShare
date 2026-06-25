import os, pytz, re, datetime, logging, asyncio, math, time
import pymongo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, Unauthorized
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Ensure these match your actual info.py exports
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL, DATABASE_NAME
from info import DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5

# Import tempDict to control DB routing dynamically
from sample_info import tempDict

# Import the single save_file function and the DB switcher
from database.ia_filterdb import save_file, check_file, get_readable_time, choose_mediaDB
from utils import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

# MongoDB setup for tracking index progress (so you don't lose progress if the VPS crashes)
inclient = pymongo.MongoClient(DATABASE_URI)
indb = inclient[DATABASE_NAME]
incol = indb['index']

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing")
    
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been declined by our moderators.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Wait until the previous process completes.', show_alert=True)
    
    msg = query.message
    await query.answer('Processing...⏳', show_alert=True)
    
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                               reply_to_message_id=int(lst_msg_id))
        
    await msg.edit(
        "Starting Indexing...",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
        )
    )
    
    try:
        chat = int(chat)
    except ValueError:
        pass # Keep as string if it's a username

    # Route to the correct database function based on the callback data
    if raju == 'accept1':
        await index_files_to_db_single(int(lst_msg_id), chat, msg, bot, 1)
    elif raju == 'accept2':
        await index_files_to_db_single(int(lst_msg_id), chat, msg, bot, 2)
    elif raju == 'accept3':
        await index_files_to_db_single(int(lst_msg_id), chat, msg, bot, 3)
    elif raju == 'accept4':
        await index_files_to_db_single(int(lst_msg_id), chat, msg, bot, 4)
    elif raju == 'accept5':
        await index_files_to_db_all(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int("-100" + chat_id)
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return

    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')

    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        return await message.reply('Make Sure That I am An Admin In The Channel (if the channel is private).')
    
    if k.empty:
        return await message.reply('This may be a group and I am not an admin of the group.')

    if message.from_user.id in ADMINS:
        buttons = [
            [InlineKeyboardButton('Index To DB1', callback_data=f'index#accept1#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Index To DB2', callback_data=f'index#accept2#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Index To DB3', callback_data=f'index#accept3#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Index To DB4', callback_data=f'index#accept4#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Index To All DBs (Round Robin)', callback_data=f'index#accept5#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Close', callback_data='close_data')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Do you Want To Index This Channel/Group?\n\nChat ID/Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
    else:
        link = f"@{message.forward_from_chat.username}"

    buttons = [
        [InlineKeyboardButton('Accept Index', callback_data=f'index#accept5#{chat_id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#IndexRequest\n\nBy: {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\nInviteLink: {link}',
                           reply_markup=reply_markup)
    await message.reply('Thank You For the Contribution, Wait For My Moderators to verify the files.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if len(message.command) > 1:
        skip = message.command[1]
        try:
            skip = int(skip)
        except ValueError:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")


# --- INDEXING LOGIC ---

async def index_files_to_db_single(lst_msg_id, chat, msg, bot, db_num):
    """Indexes files into one specific database."""
    uri_map = {
        1: DATABASE_URI,
        2: DATABASE_URI2,
        3: DATABASE_URI3,
        4: DATABASE_URI4,
        5: DATABASE_URI5
    }
    
    tempDict['indexDB'] = uri_map.get(db_num, DATABASE_URI)
    await choose_mediaDB() 
    
    total_files = 0
    duplicate = 0
    no_media = 0
    errors = 0
    fst_msg_id = temp.CURRENT
    
    start_time = time.time()
    last_update_time = time.time() # Track the last time we updated the UI
    
    remaining_time_str = "N/A"
    remaining_index = 0
    elapsed_time_str = "0s"
    
    is_unauthorized = False
    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False

            # ── BATCH FETCH: get up to 200 messages per Telegram API call ────
            BATCH = 200
            msg_ids = list(range(temp.CURRENT, lst_msg_id + 1))

            for batch_start in range(0, len(msg_ids), BATCH):
                if temp.CANCEL:
                    break

                batch_ids = msg_ids[batch_start: batch_start + BATCH]
                try:
                    messages = await bot.get_messages(chat, batch_ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    messages = await bot.get_messages(chat, batch_ids)

                for message in messages:
                    if temp.CANCEL:
                        break

                    current += 1

                    # ── UI UPDATE every 20 seconds ───────────────────────────
                    if time.time() - last_update_time >= 20:
                        last_update_time = time.time()
                        tz = pytz.timezone('Asia/Kolkata')
                        ttime = datetime.datetime.now(tz).strftime("%I:%M:%S %p - %d %b, %Y")
                        elapsed_time = time.time() - start_time
                        processed_count = current - fst_msg_id + 1
                        remaining_time = (lst_msg_id - current) * (elapsed_time / processed_count) if processed_count > 0 else 0
                        remaining_time_str = get_readable_time(remaining_time)
                        elapsed_time_str = get_readable_time(elapsed_time)
                        remaining_index = lst_msg_id - current
                        reply = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
                        try:
                            await msg.edit_text(
                                f"<b>╭ ▸ ETC: </b>{remaining_time_str} ❙ <b>Remaining:</b> <code>{remaining_index}</code>\n"
                                f"<b>├ ▸ Last Updated: <i>{ttime}</i></b>\n"
                                f"<b>╰ ▸ Time Taken: </b>{elapsed_time_str}\n\n"
                                f"<b>╭ ▸ Fetched:</b> <code>{current}</code>\n"
                                f"<b>├ ▸ Saved:</b> <code>{total_files}</code>\n"
                                f"<b>├ ▸ Duplicate:</b> <code>{duplicate}</code>\n"
                                f"<b>╰ ▸ Non/Errors:</b> <code>{no_media + errors}</code>\n",
                                reply_markup=reply)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)

                    if message.empty or not message.media or message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                        no_media += 1
                        continue

                    media = getattr(message, message.media.value, None)
                    filename = getattr(media, "file_name", "") or ""
                    mime_type = getattr(media, "mime_type", "") or ""
                    if not media or not (
                        filename.lower().endswith(('.mkv', '.mp4', '.avi', '.webm', '.mov', '.ts', '.m4v', '.3gp')) or
                        mime_type.lower().startswith(('video/', 'audio/')) or
                        mime_type.lower() in ['application/x-matroska', 'application/octet-stream']
                    ):
                        no_media += 1
                        continue

                    media.file_type = message.media.value
                    media.caption = message.caption

                    if await check_file(media) == "okda":
                        aynav, vnay = await save_file(media)
                        if aynav: total_files += 1
                        elif vnay == 0: duplicate += 1
                        elif vnay == 2: errors += 1
                    else:
                        duplicate += 1

                # Yield to event loop between batches so bot stays responsive
                await asyncio.sleep(0)

        except Unauthorized as e:
            logger.error(f"Unauthorized error during indexing (single): {e}")
            is_unauthorized = True
        except Exception as e:
            logger.exception(e)
            try:
                await msg.edit_text(f'<b>🚫 Error:</b> {e}')
            except Exception as edit_err:
                logger.error(f"Failed to edit message with error text in index_files_to_db_single: {edit_err}")
        finally:
            if not is_unauthorized:
                status = "❌ Cancelled" if temp.CANCEL else "✅ Completed"
                tz = pytz.timezone('Asia/Kolkata')
                ttime = datetime.datetime.now(tz).strftime("%I:%M:%S %p - %d %b, %Y")
                try:
                    await msg.edit_text(
                        f"<b>{status}!!</b>\n\n"
                        f"<b>├ ▸ Last Updated: <i>{ttime}</i></b>\n"
                        f"<b>╰ ▸ Time Taken: </b>{elapsed_time_str}\n\n"
                        f"<b>╭ ▸ Fetched:</b> <code>{current}</code>\n"
                        f"<b>├ ▸ Saved:</b> <code>{total_files}</code>\n"
                        f"<b>├ ▸ Duplicate:</b> <code>{duplicate}</code>\n"
                        f"<b>╰ ▸ Non/Errors:</b> <code>{no_media + errors}</code>\n"
                    )
                except Exception as edit_err:
                    logger.error(f"Failed to edit message in finally block of index_files_to_db_single: {edit_err}")


async def index_files_to_db_all(lst_msg_id, chat, msg, bot):
    """Indexes files distributing them evenly across all 5 databases (Round-Robin)."""
    db_uris = [DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5]
    
    total_files = 0
    duplicate = 0
    no_media = 0
    errors = 0
    fst_msg_id = temp.CURRENT
    
    start_time = time.time()
    last_update_time = time.time() # Track the last time we updated the UI
    
    remaining_time_str = "N/A"
    remaining_index = 0
    elapsed_time_str = "0s"
    
    is_unauthorized = False
    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False

            # ── BATCH FETCH: 200 messages per Telegram API call ───────────────
            BATCH = 200
            msg_ids = list(range(temp.CURRENT, lst_msg_id + 1))

            for batch_start in range(0, len(msg_ids), BATCH):
                if temp.CANCEL:
                    break

                batch_ids = msg_ids[batch_start: batch_start + BATCH]
                try:
                    messages = await bot.get_messages(chat, batch_ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    messages = await bot.get_messages(chat, batch_ids)

                for message in messages:
                    if temp.CANCEL:
                        break

                    current += 1

                    # ── UI + Mongo progress update every 20 seconds ──────────
                    if time.time() - last_update_time >= 20:
                        last_update_time = time.time()
                        tz = pytz.timezone('Asia/Kolkata')
                        ttime = datetime.datetime.now(tz).strftime("%I:%M:%S %p - %d %b, %Y")
                        elapsed_time = time.time() - start_time
                        processed_count = current - fst_msg_id + 1
                        remaining_time = (lst_msg_id - current) * (elapsed_time / processed_count) if processed_count > 0 else 0
                        remaining_time_str = get_readable_time(remaining_time)
                        elapsed_time_str = get_readable_time(elapsed_time)
                        remaining_index = lst_msg_id - current

                        incol.update_one(
                            {"_id": "index_progress"},
                            {"$set": {"last_indexed_file": current, "last_msg_id": lst_msg_id, "chat_id": chat}},
                            upsert=True
                        )

                        reply = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
                        try:
                            await msg.edit_text(
                                f"<b>╭ ▸ ETC: </b>{remaining_time_str} ❙ <b>Remaining:</b> <code>{remaining_index}</code>\n"
                                f"<b>├ ▸ Last Updated: <i>{ttime}</i></b>\n"
                                f"<b>╰ ▸ Time Taken: </b>{elapsed_time_str}\n\n"
                                f"<b>╭ ▸ Fetched:</b> <code>{current}</code>\n"
                                f"<b>├ ▸ Saved:</b> <code>{total_files}</code>\n"
                                f"<b>├ ▸ Duplicate:</b> <code>{duplicate}</code>\n"
                                f"<b>╰ ▸ Non/Errors:</b> <code>{no_media + errors}</code>\n",
                                reply_markup=reply)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)

                    if message.empty or not message.media or message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                        no_media += 1
                        continue

                    media = getattr(message, message.media.value, None)
                    filename = getattr(media, "file_name", "") or ""
                    mime_type = getattr(media, "mime_type", "") or ""
                    if not media or not (
                        filename.lower().endswith(('.mkv', '.mp4', '.avi', '.webm', '.mov', '.ts', '.m4v', '.3gp')) or
                        mime_type.lower().startswith(('video/', 'audio/')) or
                        mime_type.lower() in ['application/x-matroska', 'application/octet-stream']
                    ):
                        no_media += 1
                        continue

                    media.file_type = message.media.value
                    media.caption = message.caption

                    if await check_file(media) == "okda":
                        tempDict['indexDB'] = db_uris[current % 5]
                        await choose_mediaDB()
                        aynav, vnay = await save_file(media)
                        if aynav: total_files += 1
                        elif vnay == 0: duplicate += 1
                        elif vnay == 2: errors += 1
                    else:
                        duplicate += 1

                # Yield to event loop between batches so bot stays responsive
                await asyncio.sleep(0)
        except Unauthorized as e:
            logger.error(f"Unauthorized error during indexing (all): {e}")
            is_unauthorized = True
        except Exception as e:
            logger.exception(e)
            try:
                await msg.edit_text(f'<b>🚫 Error:</b> {e}')
            except Exception as edit_err:
                logger.error(f"Failed to edit message with error text in index_files_to_db_all: {edit_err}")
        finally:
            if not is_unauthorized:
                status = "❌ Cancelled" if temp.CANCEL else "✅ Completed"
                tz = pytz.timezone('Asia/Kolkata')
                ttime = datetime.datetime.now(tz).strftime("%I:%M:%S %p - %d %b, %Y")
                try:
                    await msg.edit_text(
                        f"<b>{status}!!</b>\n\n"
                        f"<b>├ ▸ Last Updated: <i>{ttime}</i></b>\n"
                        f"<b>╰ ▸ Time Taken: </b>{elapsed_time_str}\n\n"
                        f"<b>╭ ▸ Fetched:</b> <code>{current}</code>\n"
                        f"<b>├ ▸ Saved:</b> <code>{total_files}</code>\n"
                        f"<b>├ ▸ Duplicate:</b> <code>{duplicate}</code>\n"
                        f"<b>╰ ▸ Non/Errors:</b> <code>{no_media + errors}</code>\n"
                    )
                except Exception as edit_err:
                    logger.error(f"Failed to edit message in finally block of index_files_to_db_all: {edit_err}")
            if not temp.CANCEL:
                incol.delete_one({"_id": "index_progress"})
