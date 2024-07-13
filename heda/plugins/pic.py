from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait
import asyncio
import os
import logging

# Loglama ayarları
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("pic"))
async def get_profile_photos(client: Client, message: Message):
    async def send_media_group_with_retry(chat_id, media):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return await client.send_media_group(chat_id, media=media)
            except FloodWait as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(e.value)

    try:
        if message.reply_to_message:
            target = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            target = message.command[1]
        else:
            await message.reply("Lütfen bir kullanıcı ID'si, kullanıcı adı belirtin veya bir mesajı yanıtlayın.")
            return

        user = await client.get_users(target)
        
        media = []
        async for photo in client.get_chat_photos(user.id):
            file = await client.download_media(photo.file_id)
            file_extension = os.path.splitext(file)[1].lower()
            
            if file_extension in ['.mp4', '.webm']:
                media.append(InputMediaVideo(file))
            else:
                media.append(InputMediaPhoto(file))

        if not media:
            await message.reply("Bu kullanıcının profil fotoğrafı yok.")
            return

        # Son medya öğesine açıklama ekleme
        media[-1].caption = f"{user.first_name} kullanıcısının {len(media)} adet profil fotoğrafı."

        # Tüm medyayı tek seferde gönderme
        await send_media_group_with_retry(message.chat.id, media)

    except Exception as e:
        logger.error(f"Bir hata oluştu: {str(e)}")
        await message.reply("İşlem sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyiniz.")

    finally:
        # Temizlik işlemleri
        for file in os.listdir():
            if file.startswith("profile_photo_") or file.startswith("profile_video_"):
                try:
                    os.remove(file)
                except Exception as e:
                    logger.error(f"Dosya silinirken hata oluştu: {str(e)}")
                    
