import os
import zipfile
import tempfile
import libarchive.public
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
                # libarchive kullanarak dosyayı çıkar
                with libarchive.public.file_reader(zip_path) as e:
                    for entry in e:
                        with open(os.path.join(temp_dir, entry.pathname), 'wb') as f:
                            for block in entry.get_blocks():
                                f.write(block)

            # Çıkarılan dosyaları kullanıcıya gönder
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 0:
                        await client.send_document(message.chat.id, file_path)
                    else:
                        await message.reply(f"{file} dosyası boş olduğu için gönderilemiyor.")

        except (zipfile.BadZipFile, libarchive.exception.ArchiveError):
            await message.reply("Geçersiz bir dosya.")
        finally:
            # İndirilen zip dosyasını sil
            os.remove(zip_path)
            
