import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import yt_dlp

# Video kalite seçenekleri
QUALITIES = [360, 480, 720, 1080, 1440, 2160]

def create_quality_buttons(video_url):
    buttons = []
    for quality in QUALITIES:
        buttons.append([InlineKeyboardButton(f"{quality}p", callback_data=f"quality_{quality}_{video_url}")])
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("yt"))
async def yt_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("Lütfen bir YouTube linki girin. Örnek: /yt https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        return

    video_url = message.command[1]
    reply_markup = create_quality_buttons(video_url)
    await message.reply_text("Lütfen bir video kalitesi seçin:", reply_markup=reply_markup)

@Client.on_callback_query(filters.regex(r'^quality_(\d+)_(.+)$'))
async def callback_query_handler(client, callback_query: CallbackQuery):
    quality = callback_query.matches[0].group(1)
    video_url = callback_query.matches[0].group(2)
    await download_and_send_video(client, callback_query, video_url, quality)

async def download_and_send_video(client, callback_query, video_url, quality):
    await callback_query.answer("Video indiriliyor ve gönderiliyor...")

    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': '%(title)s.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info['title']
            file_name = ydl.prepare_filename(info)

        await callback_query.edit_message_text(f"'{video_title}' indiriliyor...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        await callback_query.edit_message_text(f"'{video_title}' gönderiliyor...")

        await client.send_video(
            chat_id=callback_query.message.chat.id,
            video=file_name,
            caption=f"{video_title}\n\nKalite: {quality}p",
            supports_streaming=True
        )

        os.remove(file_name)
        await callback_query.edit_message_text(f"'{video_title}' başarıyla gönderildi!")

    except Exception as e:
        await callback_query.edit_message_text(f"Video indirilirken bir hata oluştu: {str(e)}")
