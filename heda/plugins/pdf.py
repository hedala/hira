import asyncio
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from pdf2image import convert_from_path
from io import BytesIO

@Client.on_message(filters.command("pdf"))
async def send_pdf_pages(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Lütfen bir PDF dosyasına yanıt vererek /pdf komutunu kullanın.")
        return

    pdf_document = message.reply_to_message.document
    if not pdf_document.file_name.endswith(".pdf"):
        await message.reply("Lütfen geçerli bir PDF dosyasına yanıt verin.")
        return

    # PDF dosyasını indirin
    pdf_path = await client.download_media(pdf_document)

    # İlk 5 sayfayı görüntüye dönüştürün
    images = convert_from_path(pdf_path, first_page=1, last_page=5)

    # Görselleri medyaya dönüştürün
    media = []
    for i, image in enumerate(images):
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        media.append(InputMediaPhoto(img_byte_arr))

    # Medya grubunu gönderin
    await client.send_media_group(message.chat.id, media)
