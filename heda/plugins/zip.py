import os
import zipfile
import pyzipper
from pyrogram import Client, filters
from pyrogram.types import Message

# Geçici dosya dizini
TEMP_DIR = "temp_files"

# Geçici dosya dizinini oluştur
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@Client.on_message(filters.command("unzip") & filters.private)
async def unzip_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("Lütfen bir zip dosyasını yanıtlayarak bu komutu kullanın.")
        return

    # Dosyayı indir
    file_path = await client.download_media(message.reply_to_message.document, file_name=TEMP_DIR)
    file_name = os.path.basename(file_path)
    extracted_dir = os.path.join(TEMP_DIR, file_name + "_extracted")

    try:
        # Dosyayı çöz
        if file_name.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
        elif file_name.endswith(".7z"):
            with pyzipper.AESZipFile(file_path, 'r') as z:
                z.extractall(path=extracted_dir)
        elif file_name.endswith(".001"):
            base_name = file_path[:-4]  # .001 uzantısını kaldır
            with open(base_name, 'wb') as output_file:
                part_num = 1
                while True:
                    part_file = f"{base_name}.{'{:03d}'.format(part_num)}"
                    if not os.path.exists(part_file):
                        break
                    with open(part_file, 'rb') as pf:
                        output_file.write(pf.read())
                    part_num += 1
            with zipfile.ZipFile(base_name, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
        else:
            await message.reply_text("Desteklenmeyen dosya formatı.")
            return

        # Çözülen dosyaları yükle
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                file_to_send = os.path.join(root, file)
                await client.send_document(message.chat.id, file_to_send)

    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {str(e)}")
    finally:
        # Geçici dosyaları temizle
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(extracted_dir):
            shutil.rmtree(extracted_dir)
