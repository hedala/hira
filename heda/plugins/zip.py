import os
import zipfile
import tempfile
from pyrogram import Client, filters

@Client.on_message(filters.command("unzip") & filters.private)
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Lütfen bir zip dosyasına yanıt verin.")
        return

    zip_document = message.reply_to_message.document

    if not zip_document.file_name.endswith(".zip"):
        await message.reply("Lütfen bir zip dosyası gönderin.")
        return

    # Dosyayı indir
    zip_path = await client.download_media(zip_document)

    # Geçici bir dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Zip dosyasını aç ve içeriğini geçici dizine çıkar
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Çıkarılan dosyaları kullanıcıya gönder
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    await client.send_document(message.chat.id, file_path)

        except zipfile.BadZipFile:
            await message.reply("Geçersiz bir zip dosyası.")
        finally:
            # İndirilen zip dosyasını sil
            os.remove(zip_path)
