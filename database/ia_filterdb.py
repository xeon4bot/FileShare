import logging
from struct import pack
import re
import base64
import asyncio
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError

# Ensure these match your info.py exports exactly
from info import (
    DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_URI4, DATABASE_URI5, 
    DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN
)
from utils import get_settings, save_group_settings
from sample_info import tempDict 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global variable to hold the currently selected database model
saveMedia = None

# --- DATABASE INSTANCE SETUP ---

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

client2 = AsyncIOMotorClient(DATABASE_URI2)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)

client3 = AsyncIOMotorClient(DATABASE_URI3)
db3 = client3[DATABASE_NAME]
instance3 = Instance.from_db(db3)

client4 = AsyncIOMotorClient(DATABASE_URI4)
db4 = client4[DATABASE_NAME]
instance4 = Instance.from_db(db4)

client5 = AsyncIOMotorClient(DATABASE_URI5)
db5 = client5[DATABASE_NAME]
instance5 = Instance.from_db(db5)

# --- MODELS SETUP ---

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance3.register
class Media3(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance4.register
class Media4(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance5.register
class Media5(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

# --- DYNAMIC DB ROUTING ---

_URI_TO_MODEL = None  # Populated lazily after models are registered

def _get_uri_map():
    global _URI_TO_MODEL
    if _URI_TO_MODEL is None:
        _URI_TO_MODEL = {
            DATABASE_URI:  Media,
            DATABASE_URI2: Media2,
            DATABASE_URI3: Media3,
            DATABASE_URI4: Media4,
            DATABASE_URI5: Media5,
        }
    return _URI_TO_MODEL

async def choose_mediaDB():
    """Chooses which database to use based on the indexDB key in tempDict."""
    global saveMedia
    saveMedia = _get_uri_map().get(tempDict.get('indexDB'), Media)
    if tempDict.get('indexDB') not in _get_uri_map():
        logger.warning("indexDB not matched or empty, falling back to Media (DB1)")

# ── OPTIMISATION: all 5 duplicate-checks run IN PARALLEL (≈5x faster) ──────
async def check_file(media):
    """
    Check if file already exists in ANY of the 5 databases.
    All 5 find_one queries fire simultaneously via asyncio.gather.
    Returns "okda" when the file is new, None when it is a duplicate.
    """
    file_id, _ = unpack_new_file_id(media.file_id)
    results = await asyncio.gather(
        Media.collection.find_one({"_id": file_id}, {"_id": 1}),
        Media2.collection.find_one({"_id": file_id}, {"_id": 1}),
        Media3.collection.find_one({"_id": file_id}, {"_id": 1}),
        Media4.collection.find_one({"_id": file_id}, {"_id": 1}),
        Media5.collection.find_one({"_id": file_id}, {"_id": 1}),
    )
    return None if any(results) else "okda"

async def save_file(media):
    """Save file dynamically in the selected database via choose_mediaDB"""
    if saveMedia is None:
        await choose_mediaDB()

    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    # Extensive cleanup regex from snippet 1
    file_name = re.sub(r"(_|\+\s|\-|\.|\+|\[MM\]\s|\[MM\]_|\@TvSeriesBay|\@Cinema\sCompany|\@Cinema_Company|\@CC_|\@CC|\@MM_New|\@MM_Linkz|\@MOVIEHUNT|\@CL|\@FBM|\@CKMSERIES|www_DVDWap_Com_|MLM|\@WMR|\[CF\]\s|\[CF\]|\@IndianMoviez|\@tamil_mm|\@infotainmentmedia|\@trolldcompany|\@Rarefilms|\@yamandanmovies|\[YM\]|\@Mallu_Movies|\@YTSLT|\@DailyMovieZhunt|\@I_M_D_B|\@CC_All|\@PM_Old|Dvdworld|\[KMH\]|\@FBM_HW|\@Film_Kottaka|\@CC_X265|\@CelluloidCineClub|\@cinemaheist|\@telugu_moviez|\@CR_Rockers|\@CCineClub|KC_|\[KC\])", " ", str(media.file_name))
    
    try:
        # Prevent exact duplicate in the currently active DB
        if await saveMedia.count_documents({'file_id': file_id}, limit=1):
            logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in the active DB!')
            return False, 0
            
        file = saveMedia(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:  
            logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in selected database')
            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to selected database')
            return True, 1

# --- SEARCH LOGIC (INTERLEAVING 5 DBS) ---

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """Queries all 5 databases, interleaves the results, and handles offsets."""
    if chat_id is not None:
        try:
            settings = await get_settings(int(chat_id))
            # Optional: Override max_results using group settings here if desired
        except Exception as e:
            logger.error(f"Settings fetch error: {e}")

    query = query.strip()

    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_]|\s|&)' + query + r'(\b|[\.\+\-_]|\s|&)'
    else:
        raw_pattern = query.replace(' ', r'.*[&\s\.\+\-_()\[\]]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return [], '', 0

    if USE_CAPTION_FILTER:
        filter_dict = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_dict = {'file_name': regex}

    if file_type:
        filter_dict['file_type'] = file_type

    if offset < 0: offset = 0

    fetch_length = offset + max_results  # how many docs to pull from each DB

    # ── Run every DB query concurrently (counts + fetches) ──────────────────
    (counts, f1, f2, f3, f4, f5) = await asyncio.gather(
        asyncio.gather(
            Media.count_documents(filter_dict),
            Media2.count_documents(filter_dict),
            Media3.count_documents(filter_dict),
            Media4.count_documents(filter_dict),
            Media5.count_documents(filter_dict),
        ),
        Media.find(filter_dict).sort('$natural', -1).to_list(length=fetch_length),
        Media2.find(filter_dict).sort('$natural', -1).to_list(length=fetch_length),
        Media3.find(filter_dict).sort('$natural', -1).to_list(length=fetch_length),
        Media4.find(filter_dict).sort('$natural', -1).to_list(length=fetch_length),
        Media5.find(filter_dict).sort('$natural', -1).to_list(length=fetch_length),
    )
    total_results = sum(counts)

    interleaved_files = []
    i1 = i2 = i3 = i4 = i5 = 0

    while (i1 < len(f1) or i2 < len(f2) or i3 < len(f3) or i4 < len(f4) or i5 < len(f5)):
        if i1 < len(f1): interleaved_files.append(f1[i1]); i1 += 1
        if i2 < len(f2): interleaved_files.append(f2[i2]); i2 += 1
        if i3 < len(f3): interleaved_files.append(f3[i3]); i3 += 1
        if i4 < len(f4): interleaved_files.append(f4[i4]); i4 += 1
        if i5 < len(f5): interleaved_files.append(f5[i5]); i5 += 1

    # Apply the slice for current offset
    files = interleaved_files[offset:offset + max_results]
    next_offset = offset + len(files)

    if next_offset >= total_results:
        next_offset = ''
        
    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, filter=False):
    """Retrieve bad files across all 5 databases"""
    query = query.strip()
    
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], 0

    if USE_CAPTION_FILTER:
        filter_dict = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_dict = {'file_name': regex}

    if file_type:
        filter_dict['file_type'] = file_type

    cursor1 = Media.find(filter_dict).sort('$natural', -1)
    cursor2 = Media2.find(filter_dict).sort('$natural', -1)
    cursor3 = Media3.find(filter_dict).sort('$natural', -1)
    cursor4 = Media4.find(filter_dict).sort('$natural', -1)
    cursor5 = Media5.find(filter_dict).sort('$natural', -1)

    # ── Fetch from all DBs concurrently ─────────────────────────────────────
    lists = await asyncio.gather(
        cursor1.to_list(length=None),
        cursor2.to_list(length=None),
        cursor3.to_list(length=None),
        cursor4.to_list(length=None),
        cursor5.to_list(length=None),
    )
    files = [f for lst in lists for f in lst]

    return files, len(files)

async def delete_files_below_threshold(db, threshold_size_mb: int = 40, batch_size: int = 20, chat_id: int = None, message_id: int = None):
    """Deletes files below a size limit from all databases"""
    limit_size = threshold_size_mb * 1024 * 1024
    models = [Media, Media2, Media3, Media4, Media5]
    total_deleted = 0
    
    for model in models:
        cursor = model.find({"file_size": {"$lt": limit_size}}).limit(batch_size // len(models))
        async for document in cursor:
            try:
                await model.collection.delete_one({"_id": document["file_id"]})
                total_deleted += 1
                logger.info(f'Deleted file from {model.__name__}: {document["file_name"]}')
            except Exception as e:
                logger.error(f'Error deleting file from {model.__name__}: {document["file_name"]}, {e}')

    return total_deleted

async def get_file_details(query):
    """Look up a file_id across all 5 databases — all queries fire concurrently."""
    filter_dict = {'file_id': query}
    results = await asyncio.gather(
        Media.find(filter_dict).to_list(length=1),
        Media2.find(filter_dict).to_list(length=1),
        Media3.find(filter_dict).to_list(length=1),
        Media4.find(filter_dict).to_list(length=1),
        Media5.find(filter_dict).to_list(length=1),
    )
    for result in results:
        if result:
            return result
    return []

# --- UTILS ---

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack("<iiqq", int(decoded.file_type), decoded.dc_id, decoded.media_id, decoded.access_hash)
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

def get_readable_time(seconds) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    if int(days) != 0: result += f"{int(days)}d"
    
    (hours, remainder) = divmod(remainder, 3600)
    if int(hours) != 0: result += f"{int(hours)}h"
    
    (minutes, seconds) = divmod(remainder, 60)
    if int(minutes) != 0: result += f"{int(minutes)}m"
    
    result += f"{int(seconds)}s"
    return result
