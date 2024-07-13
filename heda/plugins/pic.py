from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto

@Client.on_message(filters.command("pic", prefixes="/") & filters.me)
async def send_profile_pics(client, message):
    user = None

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        identifier = message.command[1]
        if identifier.isdigit():
            user = await client.get_users(int(identifier))
        else:
            user = await client.get_users(identifier)
    else:
        await message.reply_text("Kullanıcı ID veya kullanıcı adı belirtmelisiniz.")
        return

    if not user:
        await message.reply_text("Kullanıcı bulunamadı.")
        return

    photos = await client.get_profile_photos(user.id)
    if not photos:
        await message.reply_text("Bu kullanıcının profil fotoğrafı yok.")
        return

    media_groups = []
    media_group = []

    for i, photo in enumerate(photos):
        file_path = await client.download_media(photo.file_id)
        media_group.append(InputMediaPhoto(file_path))

        if len(media_group) == 10:
            media_groups.append(media_group)
            media_group = []

    if media_group:
        media_groups.append(media_group)

    for group in media_groups:
        await message.reply_media_group(group)
