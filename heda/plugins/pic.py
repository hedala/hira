from pyrogram import Client, filters
from pyrogram.types import Message
import os

@Client.on_message(filters.command("pic"))
async def get_profile_photos(client: Client, message: Message):
    # Hedef kullanıcıyı belirleme
    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        target = message.command[1]
    else:
        await message.reply("Lütfen bir kullanıcı ID'si, kullanıcı adı belirtin veya bir mesajı yanıtlayın.")
        return

    try:
        # Kullanıcı bilgilerini alma
        user = await client.get_users(target)
        
        # Profil fotoğraflarını indirme
        photos = []
        async for photo in client.get_chat_photos(user.id):
            file_path = await client.download_media(photo.file_id, file_name=f"profile_photo_{photo.file_id}.jpg")
            photos.append(file_path)

        if not photos:
            await message.reply("Bu kullanıcının profil fotoğrafı yok.")
            return

        # Fotoğrafları gruplar halinde gönderme
        for i in range(0, len(photos), 10):
            media_group = [{"type": "photo", "media": photo} for photo in photos[i:i+10]]
            await client.send_media_group(message.chat.id, media=media_group)

        # İndirilen dosyaları temizleme
        for photo in photos:
            os.remove(photo)

        await message.reply(f"{user.first_name} kullanıcısının {len(photos)} adet profil fotoğrafı gönderildi.")

    except Exception as e:
        await message.reply(f"Bir hata oluştu: {str(e)}")
                           
