import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Format ve kalite seçenekleri
video_formats = ["720p", "1080p", "2K", "4K", "Best Video"]
audio_formats = ["MP3 128 kbps", "MP3 320 kbps", "FLAC", "Best Audio"]

# İndirme işlemi için yt-dlp seçenekleri
def get_ydl_opts(format):
    ydl_opts = {
        'format': format,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }
    return ydl_opts

# İndirme ilerleme durumu
def progress_hook(d):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        message.edit_text(f"Video indiriliyor. %{percentage}")

# /yt komutu
@Client.on_message(filters.command("yt"))
async def yt_command(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Lütfen bir YouTube linki veya arama argümanı girin.")
        return

    query = args[1]
    if query.startswith("http"):
        await send_format_buttons(message, query)
    else:
        await search_youtube(message, query)

# Format ve kalite seçim butonları gönderme
async def send_format_buttons(message: Message, link: str):
    buttons = [
        [InlineKeyboardButton(f"Video: {fmt}", callback_data=f"video|{link}|{fmt}") for fmt in video_formats],
        [InlineKeyboardButton(f"Audio: {fmt}", callback_data=f"audio|{link}|{fmt}") for fmt in audio_formats],
    ]
    await message.reply("Hangi formatta indirmek istersiniz?", reply_markup=InlineKeyboardMarkup(buttons))

# YouTube'da arama yapma
async def search_youtube(message: Message, query: str):
    ydl_opts = {'default_search': 'ytsearch5', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(query, download=False)['entries']
    
    buttons = [
        [InlineKeyboardButton(result['title'], callback_data=f"search|{result['webpage_url']}") for result in results]
    ]
    await message.reply("Arama sonuçları:", reply_markup=InlineKeyboardMarkup(buttons))

# Callback butonları işleme
@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("|")
    action = data[0]
    link = data[1]
    format = data[2] if len(data) > 2 else None

    if action == "video" or action == "audio":
        await download_media(callback_query.message, link, format)
    elif action == "search":
        await send_format_buttons(callback_query.message, link)

# Medya indirme ve gönderme
async def download_media(message: Message, link: str, format: str):
    ydl_opts = get_ydl_opts(format)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        file_path = ydl.prepare_filename(info)
    
    await message.reply_document(file_path, caption=f"{info['title']} ({format})")
    os.remove(file_path)
