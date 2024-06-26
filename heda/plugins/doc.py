import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

@Client.on_message(filters.command("open"))
async def open_file(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("Lütfen bir dosya alıntılayarak komutu kullanın.")
        return

    file_id = message.reply_to_message.document.file_id
    file_path = await client.download_media(file_id)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        await message.reply_text(f"```{file_content}```", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply_text(f"Dosya okunurken hata oluştu: {e}")
    finally:
        os.remove(file_path)

@Client.on_message(filters.command("doc"))
async def doc_file(client, message: Message):
    if len(message.command) < 2 or not message.reply_to_message or not message.reply_to_message.text:
        await message.reply_text("Lütfen bir dosya adı ve metin alıntısı sağlayarak komutu kullanın.")
        return

    file_name = message.command[1]
    text = message.reply_to_message.text
    
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text)
        
        await client.send_document(
            chat_id=message.chat.id,
            document=file_name,
            caption="İşte dosyanız"
        )
    except Exception as e:
        await message.reply_text(f"Dosya oluşturulurken hata oluştu: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
