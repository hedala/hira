import os
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search_python import VideosSearch

# Video ve ses kalite seçenekleri
VIDEO_QUALITIES = ['720p', '1080p', '2K', '4K', 'Best Video']
AUDIO_QUALITIES = ['MP3 128 kbps', 'MP3 320 kbps', 'FLAC', 'Best Audio']

def format_progress_hook(d):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        app.send_message(d['chat_id'], f"Video indiriliyor: {percentage}")

async def download_video(youtube_link, quality, chat_id):
    ydl_opts = {
        'format': quality,
        'progress_hooks': [format_progress_hook],
        'outtmpl': 'video.%(ext)s'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_link, download=True)
        title = info_dict.get('title', None)
        file_extension = info_dict.get('ext', None)
        file_name = f"{title} ({quality}).{file_extension}"
        os.rename('video.' + file_extension, file_name)
    return file_name, info_dict

@Client.on_message(filters.command("yt"))
async def youtube_handler(client, message):
    query = ' '.join(message.command[1:])
    chat_id = message.chat.id

    if query.startswith("http"):
        await message.reply("Lütfen kalite seçiniz:", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(q, callback_data=f"{query}|{q}")] for q in VIDEO_QUALITIES + AUDIO_QUALITIES]
        ))
    else:
        search = VideosSearch(query, limit=5)
        results = search.result()['result']
        buttons = [
            [InlineKeyboardButton(result['title'], callback_data=f"{result['link']}|search")]
            for result in results
        ]
        await message.reply("Lütfen bir video seçiniz:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split('|')
    youtube_link = data[0]
    quality = data[1]
    chat_id = callback_query.message.chat.id

    if quality == "search":
        await callback_query.message.edit("Lütfen kalite seçiniz:", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(q, callback_data=f"{youtube_link}|{q}")] for q in VIDEO_QUALITIES + AUDIO_QUALITIES]
        ))
    else:
        await callback_query.message.edit("Video indiriliyor...")
        file_name, info_dict = await download_video(youtube_link, quality, chat_id)
        thumbnail_url = info_dict['thumbnail']
        duration = info_dict['duration']

        await client.send_photo(chat_id, thumbnail_url, caption=f"**{info_dict['title']}**\nSüre: {duration}s\nKalite: {quality}")
        await client.send_document(chat_id, file_name)
        os.remove(file_name)
