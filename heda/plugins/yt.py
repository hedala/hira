import os
import json
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch

# Command handler for /yt
@Client.on_message(filters.command("yt"))
async def yt_handler(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Please provide a YouTube link or search query.")
        return

    query = args[1]
    if query.startswith("http"):
        await send_format_buttons(client, message, query)
    else:
        await search_youtube(client, message, query)

async def send_format_buttons(client, message, url):
    buttons = [
        [InlineKeyboardButton("Video: 720p", callback_data=f"video_720p|{url}"),
         InlineKeyboardButton("Video: 1080p", callback_data=f"video_1080p|{url}")],
        [InlineKeyboardButton("Video: 2K", callback_data=f"video_2k|{url}"),
         InlineKeyboardButton("Video: 4K", callback_data=f"video_4k|{url}")],
        [InlineKeyboardButton("Best Video", callback_data=f"video_best|{url}")],
        [InlineKeyboardButton("Audio: MP3 128 kbps", callback_data=f"audio_128|{url}"),
         InlineKeyboardButton("Audio: MP3 320 kbps", callback_data=f"audio_320|{url}")],
        [InlineKeyboardButton("Audio: FLAC", callback_data=f"audio_flac|{url}"),
         InlineKeyboardButton("Best Audio", callback_data=f"audio_best|{url}")]
    ]
    await message.reply("Select the format:", reply_markup=InlineKeyboardMarkup(buttons))

async def search_youtube(client, message, query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    buttons = []
    for result in results:
        title = result['title']
        url = f"https://www.youtube.com{result['url_suffix']}"
        buttons.append([InlineKeyboardButton(title, callback_data=f"search_result|{url}")])
    await message.reply("Select a video:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    if data.startswith("video_") or data.startswith("audio_"):
        format_type, url = data.split("|")
        await download_media(client, callback_query.message, url, format_type)
    elif data.startswith("search_result|"):
        _, url = data.split("|")
        await send_format_buttons(client, callback_query.message, url)

async def download_media(client, message, url, format_type):
    format_map = {
        "video_720p": "bestvideo[height<=720]+bestaudio/best",
        "video_1080p": "bestvideo[height<=1080]+bestaudio/best",
        "video_2k": "bestvideo[height<=1440]+bestaudio/best",
        "video_4k": "bestvideo[height<=2160]+bestaudio/best",
        "video_best": "bestvideo+bestaudio/best",
        "audio_128": "bestaudio[ext=m4a]/bestaudio",
        "audio_320": "bestaudio[ext=m4a]/bestaudio",
        "audio_flac": "bestaudio[ext=flac]/bestaudio",
        "audio_best": "bestaudio/best"
    }

    ydl_opts = {
        'format': format_map[format_type],
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [lambda d: progress_hook(d, client, message)]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        await client.send_document(message.chat.id, file_path, caption=f"{info['title']}")

def progress_hook(d, client, message):
    if d['status'] == 'downloading':
        percent = d['_percent_str']
        client.send_message(message.chat.id, f"Downloading video. {percent}")
