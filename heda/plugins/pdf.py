import asyncio
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
import fitz  # PyMuPDF
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

    # PDF dosyasını açın ve ilk 10 sayfayı görüntüye dönüştürün
    pdf_document = fitz.open(pdf_path)
    media = []
    for page_number in range(min(10, len(pdf_document))):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img_byte_arr = BytesIO(pix.tobytes("jpeg"))
        media.append(InputMediaPhoto(img_byte_arr))

    # Medya grubunu gönderin
    await client.send_media_group(message.chat.id, media)
