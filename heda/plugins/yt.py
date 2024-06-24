import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from youtube_search import YoutubeSearch

# Function to download video/audio
def download_media(url, format_id):
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info_dict), info_dict

# Progress hook to send download progress
def progress_hook(d):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        Client.send_message(chat_id, f"Video indiriliyor. %{percentage}")

@Client.on_message(filters.command("yt"))
async def yt_command(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) == 2:
        query = args[1]
        if query.startswith("http"):
            await send_format_options(message.chat.id, query)
        else:
            await search_youtube(message.chat.id, query)
    else:
        await message.reply("Lütfen bir YouTube linki veya arama terimi girin.")

async def send_format_options(chat_id, url):
    buttons = [
        [InlineKeyboardButton("Video", callback_data=f"video|{url}")],
        [InlineKeyboardButton("Audio", callback_data=f"audio|{url}")]
    ]
    await Client.send_message(chat_id, "İndirme formatını seçin:", reply_markup=InlineKeyboardMarkup(buttons))

async def search_youtube(chat_id, query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    buttons = [[InlineKeyboardButton(result['title'], callback_data=f"select|{result['url_suffix']}")] for result in results]
    await Client.send_message(chat_id, "Arama sonuçları:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("|")
    action = data[0]
    url = data[1]

    if action == "video":
        buttons = [
            [InlineKeyboardButton("720p", callback_data=f"download|{url}|bestvideo[height<=720]")],
            [InlineKeyboardButton("1080p", callback_data=f"download|{url}|bestvideo[height<=1080]")],
            [InlineKeyboardButton("2K", callback_data=f"download|{url}|bestvideo[height<=1440]")],
            [InlineKeyboardButton("4K", callback_data=f"download|{url}|bestvideo[height<=2160]")],
            [InlineKeyboardButton("Best", callback_data=f"download|{url}|bestvideo")]
        ]
        await callback_query.message.edit_text("Video kalitesini seçin:", reply_markup=InlineKeyboardMarkup(buttons))
    elif action == "audio":
        buttons = [
            [InlineKeyboardButton("MP3 128kbps", callback_data=f"download|{url}|bestaudio[ext=mp3]/bestaudio[abr<=128]")],
            [InlineKeyboardButton("MP3 320kbps", callback_data=f"download|{url}|bestaudio[ext=mp3]/bestaudio[abr<=320]")],
            [InlineKeyboardButton("FLAC", callback_data=f"download|{url}|bestaudio[ext=flac]")],
            [InlineKeyboardButton("Best", callback_data=f"download|{url}|bestaudio")]
        ]
        await callback_query.message.edit_text("Ses kalitesini seçin:", reply_markup=InlineKeyboardMarkup(buttons))
    elif action == "download":
        format_id = data[2]
        file_path, info_dict = download_media(url, format_id)
        await Client.send_document(callback_query.message.chat.id, file_path, caption=f"{info_dict['title']} - {format_id}")
        os.remove(file_path)
