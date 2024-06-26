import os
import zipfile
import tempfile
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import time

async def progress(current, total, message: Message, action: str):
    try:
        percentage = current * 100 / total
        progress_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
        await message.edit_text(f"{action}: {percentage:.1f}%\n[{progress_bar}]")
    except FloodWait as e:
        time.sleep(e.x)

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

    # İndirme ilerlemesini gösteren mesaj
    progress_message = await message.reply("Dosya indiriliyor... 🏃‍♂️")

    # Dosyayı indir
    zip_path = await client.download_media(
        zip_document,
        progress=progress,
        progress_args=(progress_message, "İndirme")
    )

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
                    if os.path.getsize(file_path) > 0:
                        # Yükleme ilerlemesini gösteren mesaj
                        upload_progress_message = await message.reply(f"{file} yükleniyor... 🚀")
                        await client.send_document(
                            message.chat.id,
                            file_path,
                            progress=progress,
                            progress_args=(upload_progress_message, "Yükleme")
                        )
                        await upload_progress_message.delete()
                    else:
                        await message.reply(f"{file} dosyası boş olduğu için gönderilemiyor.")

        except (zipfile.BadZipFile, subprocess.CalledProcessError):
            await message.reply("Geçersiz bir dosya.")
        finally:
            # İndirilen zip dosyasını sil
            os.remove(zip_path)

    # İndirme ilerlemesi mesajını sil
    await progress_message.delete()
    
