from pyrogram import Client, filters
from info import CHANNELS, DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5
from database.ia_filterdb import save_file, check_file, choose_mediaDB
from sample_info import tempDict

media_filter = filters.document | filters.video | filters.audio

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    media.file_type = file_type
    media.caption = message.caption
    
    tru = await check_file(media)
    if tru == "okda":
        # Put all 5 URIs in a list
        db_uris = [DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5]
        
        # Distribute the files evenly across the 5 databases using the message ID
        tempDict['indexDB'] = db_uris[message.id % 5]
        await choose_mediaDB() # Force the db filter to recognize the change
        
        # Save the file to the chosen database
        await save_file(media)
    else:
        print("skipped duplicate file from saving to db 😌")
