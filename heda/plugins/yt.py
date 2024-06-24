import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import asyncio

# YouTube arama fonksiyonu
async def search_youtube(query):
    ydl_opts = {"quiet": True, "no_warnings": True}
    with YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
            return search_results
        except Exception as e:
            print(f"YouTube arama hatası: {e}")
            return []

# İndirme fonksiyonu
async def download_youtube(link, format_id, message):
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [lambda d: progress_hook(d, message)],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
    return filename, info

# İlerleme durumu için hook fonksiyonu
async def progress_hook(d, message):
    if d['status'] == 'downloading':
        percent = d['_percent_str']
        await message.edit_text(f"Video indiriliyor. {percent}")

# /yt komutu için handler
@Client.on_message(filters.command("yt"))
async def youtube_command(client, message):
    command = message.text.split(maxsplit=1)
    if len(command) == 1:
        await message.reply_text("Lütfen bir YouTube linki veya arama terimi girin.")
        return

    query = command[1]
    if "youtube.com" in query or "youtu.be" in query:
        # Link verilmişse
        await show_format_buttons(message, query)
    else:
        # Arama terimi verilmişse
        results = await search_youtube(query)
        if results:
            buttons = []
            for i, video in enumerate(results):
                buttons.append([InlineKeyboardButton(video['title'], callback_data=f"search_{i}_{query}")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text("Arama sonuçları:", reply_markup=reply_markup)
        else:
            await message.reply_text("Arama sonucu bulunamadı.")

# Format seçimi için butonları gösterme fonksiyonu
async def show_format_buttons(message, link):
    buttons = [
        [InlineKeyboardButton("Video 720p", callback_data=f"format_720_{link}")],
        [InlineKeyboardButton("Video 1080p", callback_data=f"format_1080_{link}")],
        [InlineKeyboardButton("Video 2K", callback_data=f"format_1440_{link}")],
        [InlineKeyboardButton("Video 4K", callback_data=f"format_2160_{link}")],
        [InlineKeyboardButton("Best Video", callback_data=f"format_bestvideo_{link}")],
        [InlineKeyboardButton("Audio MP3 128kbps", callback_data=f"format_mp3_128_{link}")],
        [InlineKeyboardButton("Audio MP3 320kbps", callback_data=f"format_mp3_320_{link}")],
        [InlineKeyboardButton("Audio FLAC", callback_data=f"format_flac_{link}")],
        [InlineKeyboardButton("Best Audio", callback_data=f"format_bestaudio_{link}")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text("Lütfen indirme formatını seçin:", reply_markup=reply_markup)

# Callback query handler
@Client.on_callback_query(filters.regex("^(format|search)_"))
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("_")
    if data[0] == "format":
        format_id = data[1]
        link = "_".join(data[2:])
        await process_download(callback_query.message, link, format_id)
    elif data[0] == "search":
        index = int(data[1])
        query = "_".join(data[2:])
        results = await search_youtube(query)
        if index < len(results):
            video = results[index]
            await show_format_buttons(callback_query.message, video['webpage_url'])
        else:
            await callback_query.answer("Video bulunamadı.")
            

# İndirme işlemi
async def process_download(message, link, format_id):
    progress_message = await message.reply_text("İndirme başlatılıyor...")
    try:
        filename, info = await download_youtube(link, format_id, progress_message)
        
        if 'video' in format_id:
            await message.reply_video(
                video=filename,
                caption=f"{info['title']} - {format_id}",
                duration=info.get('duration'),
                thumb=info.get('thumbnail'),
            )
        else:
            await message.reply_audio(
                audio=filename,
                caption=f"{info['title']} - {format_id}",
                duration=info.get('duration'),
            )
        
        os.remove(filename)
        await progress_message.delete()
    except Exception as e:
        await progress_message.edit_text(f"İndirme hatası: {str(e)}")
