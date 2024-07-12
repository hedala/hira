from pyrogram import Client, filters
import rarfile
import os
import tempfile

# RAR dosyalarını açmak için yeni komut
@Client.on_message(filters.command("rar"))
async def extract_rar(client, message):
    # Dosya eki kontrolü
    if not message.document or not message.document.file_name.endswith('.rar'):
        await message.reply("Please send a RAR file with the /rar command.")
        return

    # Geçici dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        # RAR dosyasını indir
        file_path = await message.download(file_name=os.path.join(temp_dir, "archive.rar"))
        
        try:
            # RAR dosyasını aç
            with rarfile.RarFile(file_path) as rf:
                # İçerik listesini al
                file_list = rf.namelist()
                
                # İçerik listesini gönder
                await message.reply(f"Contents of the RAR file:\n\n{', '.join(file_list)}")
                
                # Her dosyayı çıkar ve gönder
                for file in file_list:
                    extracted_path = os.path.join(temp_dir, file)
                    rf.extract(file, path=temp_dir)
                    
                    # Dosyayı gönder
                    await client.send_document(message.chat.id, extracted_path)
        
        except rarfile.Error as e:
            await message.reply(f"Error extracting RAR file: {str(e)}")
        except Exception as e:
            await message.reply(f"An unexpected error occurred: {str(e)}")
