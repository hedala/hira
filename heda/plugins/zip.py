import os
import zipfile
import tempfile
import subprocess
from pyrogram import Client, filters

@Client.on_message(filters.command("unzip") & filters.private)
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Lütfen bir zip dosyasına yanıt verin.")
        return

    zip_document = message.reply_to_message.document
    file_name = zip_document.file_name

    if not (file_name.endswith(".zip") or file_name.endswith(".zip.001") or file_name.endswith(".7z")):
        await message.reply("Lütfen bir zip, zip.001 veya 7z dosyası gönderin.")
        return

    # Dosyayı indir
    zip_path = await client.download_media(zip_document)

    # Geçici bir dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            if file_name.endswith(".zip"):
                # Zip dosyasını aç ve içeriğini geçici dizine çıkar
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif file_name.endswith(".zip.001") or file_name.endswith(".7z"):
                # 7-Zip komut satırı aracını kullanarak dosyayı çıkar
                subprocess.run(['7z', 'x', zip_path, f'-o{temp_dir}'], check=True)

            # Çıkarılan dosyaları kullanıcıya gönder
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    await client.send_document(message.chat.id, file_path)

        except (zipfile.BadZipFile, subprocess.CalledProcessError):
            await message.reply("Geçersiz bir dosya.")
        finally:
            # İndirilen zip dosyasını sil
            os.remove(zip_path)
