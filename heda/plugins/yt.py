from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os

# Function to get video qualities
def get_video_qualities(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        qualities = {}
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                quality = f.get('format_note')
                if quality in ['2160p', '1440p', '1080p', '720p']:
                    qualities[quality] = f.get('format_id')
        return qualities

@Client.on_message(filters.command("yt"))
async def yt_command(client, message):
    url = message.text.split(" ", 1)[1]
    qualities = get_video_qualities(url)
    buttons = [
        [InlineKeyboardButton(quality, callback_data=f"{url}|{format_id}")]
        for quality, format_id in qualities.items()
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Choose the quality:", reply_markup=reply_markup)

# Function to download video
def download_video(url, format_id):
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info_dict)

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("|")
    url, format_id = data[0], data[1]
    await callback_query.message.edit_text("Downloading...")
    video_path = download_video(url, format_id)
    await client.send_video(callback_query.message.chat.id, video=video_path)
    os.remove(video_path)
    
