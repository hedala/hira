import asyncio
import json
import time
import logging
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatWriteForbidden
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Heroku environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
MONGO_URI = os.getenv("MONGO_URI")

app = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.userbot
channels_collection = db.channels

async def get_channels():
    cursor = channels_collection.find({})
    channels = await cursor.to_list(length=None)
    return [channel['_id'] for channel in channels]

async def add_channel(channel):
    await channels_collection.update_one({'_id': channel}, {'$set': {}}, upsert=True)

async def remove_channel(channel):
    result = await channels_collection.delete_one({'_id': channel})
    return result.deleted_count > 0

async def ddg_invoke(prompt):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Accept": "text/event-stream",
        "Accept-Language": "en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://duckduckgo.com/",
        "Content-Type": "application/json",
        "Origin": "https://duckduckgo.com",
        "Connection": "keep-alive",
        "Cookie": "dcm=1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "TE": "trailers",
        "x-vqd-accept": "1",
        "Cache-Control": "no-store",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("https://duckduckgo.com/duckchat/v1/status", headers=headers) as response:
            token = response.headers["x-vqd-4"]
            headers["x-vqd-4"] = token

        url = "https://duckduckgo.com/duckchat/v1/chat"
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        }

        async with session.post(url, headers=headers, json=data) as response:
            text = await response.text()

    ret = ""
    for line in text.split("\n"):
        if len(line) > 0 and line[6] == "{":
            dat = json.loads(line[6:])
            if "message" in dat:
                ret += dat["message"].replace("\\n", "\n")

    return ret

@app.on_message(filters.command("cm", prefixes=".") & filters.me)
async def add_channel_command(client, message: Message):
    try:
        if len(message.command) != 2:
            await message.edit_text("Kullanım: .cm <kanal_id/username>")
            return
        
        channel = message.command[1]
        await add_channel(channel)
        await message.edit_text(f"Hedef kanal eklendi: {channel}")
    except Exception as e:
        logger.error(f"Kanal eklenirken hata oluştu: {e}")
        await message.delete()

@app.on_message(filters.command("cmall", prefixes=".") & filters.me)
async def list_channels(client, message: Message):
    try:
        channels = await get_channels()
        if not channels:
            await message.edit_text("Hiç kanal eklenmemiş.")
            return
        
        text = "Eklenen kanallar:\n\n"
        for channel in channels:
            text += f"• {channel}\n"
        
        await message.edit_text(text)
    except Exception as e:
        logger.error(f"Kanal listesi alınırken hata oluştu: {e}")
        await message.delete()

@app.on_message(filters.command("cmdel", prefixes=".") & filters.me)
async def delete_channel(client, message: Message):
    try:
        if len(message.command) != 2:
            await message.edit_text("Kullanım: .cmdel <kanal_id/username>")
            return
        
        channel = message.command[1]
        if await remove_channel(channel):
            await message.edit_text(f"{channel} kanalı başarıyla silindi.")
        else:
            await message.edit_text(f"{channel} kanalı bulunamadı.")
    except Exception as e:
        logger.error(f"Kanal silinirken hata oluştu: {e}")
        await message.delete()

@app.on_message(filters.channel)
async def auto_comment(client, message: Message):
    channels = await get_channels()
    channel_id = str(message.chat.id)
    channel_username = message.chat.username
    
    if channel_id in channels or (channel_username and f"@{channel_username}" in channels):
        try:
            content = message.text or message.caption or "Bu gönderide metin yok."
            
            prompt = f"""Aşağıdaki mesaj için mizah seviyesi yüksek, kısa ve eğlenceli bir yorum yaz. 
            Muhalif bir bakış açısıyla yaklaş. Eğer haber üzücüyse, empati kur ve duygusal bir yorum yap. 
            İktidarın hataları ile ilgiliyse, ciddi ama mizahi bir eleştiri yap. İnsancıl ve samimi ol. 
            Tırnak işareti kullanma. Yanıtı direkt olarak ver:

            {content}"""
            
            comment = await ddg_invoke(prompt)
            
            await asyncio.sleep(2)
            discussion_message = await client.get_discussion_message(message.chat.id, message.id)
            await discussion_message.reply(comment)
        except FloodWait as e:
            logger.warning(f"FloodWait: {e.x} saniye bekleniyor.")
            await asyncio.sleep(e.x)
        except ChatWriteForbidden:
            logger.error(f"Bu kanala yorum yapma izni yok: {message.chat.title}")
        except Exception as e:
            logger.error(f"Yorum gönderilirken hata oluştu: {e}")

print("Userbot başlatılıyor...")
app.run()
