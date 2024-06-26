import os
import zipfile
import tempfile
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import time

MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB

async def progress(current, total, message: Message, action: str, last_percentage: list):
    try:
        if total == 0:
            percentage = 0
        else:
            percentage = current * 100 / total
        if int(percentage) != last_percentage[0]:
            last_percentage[0] = int(percentage)
            progress_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
            await message.edit_text(f"{action}: {percentage:.1f}%\n[{progress_bar}]")
    except FloodWait as e:
        time.sleep(e.x)

async def extract_and_send(client, message, file_path, temp_dir):
    try:
        if file_path.endswith(".zip"):
            # Zip dosyasını aç ve içeriğini geçici dizine çıkar
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        elif file_path.endswith(".zip.001") or file_path.endswith(".7z") or file_path.endswith(".rar"):
            # 7-Zip komut satırı aracını kullanarak dosyayı çıkar
            try:
                subprocess.run(['7z', 'x', file_path, f'-o{temp_dir}'], check=True)
            except FileNotFoundError:
                await message.reply("7z komutu bulunamadı. Lütfen 7-Zip'in kurulu olduğundan ve PATH değişkenine eklendiğinden emin olun.")
                return

        # Çıkarılan dosyaları kullanıcıya gönder
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                extracted_file_path = os.path.join(root, file)
                if os.path.getsize(extracted_file_path) > 0:
                    # Yükleme ilerlemesini gösteren mesaj
                    upload_progress_message = await message.reply(f"{file} yükleniyor... 🚀")
                    last_percentage = [0]
                    await client.send_document(
                        message.chat.id,
                        extracted_file_path,
                        progress=progress,
                        progress_args=(upload_progress_message, "Yükleme", last_percentage)
                    )
                    await upload_progress_message.delete()
                else:
                    await message.reply(f"{file} dosyası boş olduğu için gönderilemiyor.")
    except (zipfile.BadZipFile, subprocess.CalledProcessError) as e:
        await message.reply(f"Geçersiz bir dosya: {str(e)}")

@Client.on_message(filters.command("unzip") & filters.private)
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Lütfen bir zip dosyasına yanıt verin.")
        return

    zip_document = message.reply_to_message.document
    file_name = zip_document.file_name
    file_size = zip_document.file_size

    if not (file_name.endswith(".zip") or file_name.endswith(".zip.001") or file_name.endswith(".7z")):
        await message.reply("Lütfen bir zip, zip.001 veya 7z dosyası gönderin.")
        return

    if file_size > MAX_FILE_SIZE:
        await message.reply("Dosya boyutu 4GB'ı aşamaz.")
        return

    # Dosya bilgilerini göster
    info_message = await message.reply(
        f"Dosya Adı: {file_name}\n"
        f"Dosya Boyutu: {file_size / (1024 * 1024):.2f} MB\n"
        "İndirme 5 saniye içinde başlayacak..."
    )

    # 5 saniye bekle
    await asyncio.sleep(5)

    # İndirme ilerlemesini gösteren mesaj
    progress_message = await message.reply("Dosya indiriliyor... 🏃‍♂️")
    last_percentage = [0]

    # Dosyayı indir
    try:
        zip_path = await client.download_media(
            zip_document,
            progress=progress,
            progress_args=(progress_message, "İndirme", last_percentage)
        )
    except Exception as e:
        await progress_message.edit_text(f"İndirme hatası: {str(e)}")
        return

    # Geçici bir dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        await extract_and_send(client, message, zip_path, temp_dir)

    # İndirme ilerlemesi mesajını sil
    await progress_message.delete()
    await info_message.delete()

@Client.on_message(filters.command("rar") & filters.private)
async def rar_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Lütfen bir rar dosyasına yanıt verin.")
        return

    rar_document = message.reply_to_message.document
    file_name = rar_document.file_name
    file_size = rar_document.file_size

    if not file_name.endswith(".rar"):
        await message.reply("Lütfen bir rar dosyası gönderin.")
        return

    if file_size > MAX_FILE_SIZE:
        await message.reply("Dosya boyutu 4GB'ı aşamaz.")
        return

    # Dosya bilgilerini göster
    info_message = await message.reply(
        f"Dosya Adı: {file_name}\n"
        f"Dosya Boyutu: {file_size / (1024 * 1024):.2f} MB\n"
        "İndirme 5 saniye içinde başlayacak..."
    )

    # 5 saniye bekle
    await asyncio.sleep(5)

    # İndirme ilerlemesini gösteren mesaj
    progress_message = await message.reply("Dosya indiriliyor... 🏃‍♂️")
    last_percentage = [0]

    # Dosyayı indir
    try:
        rar_path = await client.download_media(
            rar_document,
            progress=progress,
            progress_args=(progress_message, "İndirme", last_percentage)
        )
    except Exception as e:
        await progress_message.edit_text(f"İndirme hatası: {str(e)}")
        return

    # Geçici bir dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        await extract_and_send(client, message, rar_path, temp_dir)

    # İndirme ilerlemesi mesajını sil
    await progress_message.delete()
    await info_message.delete()
    
