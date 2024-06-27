from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

def get_video_qualities(url):
    ydl_opts = {
        'format': 'bestvideo',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        quality_buttons = []
        for f in formats:
            # Check if 'height' key exists and is one of the desired resolutions
            if 'height' in f and f['height'] in [2160, 1440, 1080, 720]:
                button = InlineKeyboardButton(f"{f['height']}p", callback_data=f"{f['format_id']}")
                quality_buttons.append(button)
        return quality_buttons

@Client.on_message(filters.command("yt") & filters.private)
def youtube_command(client, message):
    url = message.text.split(' ')[1]
    quality_buttons = get_video_qualities(url)
    reply_markup = InlineKeyboardMarkup([quality_buttons])
    message.reply_text("Choose the quality:", reply_markup=reply_markup)

@Client.on_callback_query()
def answer(client, callback_query):
    format_id = callback_query.data
    url = callback_query.message.reply_to_message.text.split(' ')[1]
    ydl_opts = {
        'format': f'{format_id}+bestaudio',
        'outtmpl': '%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        file_name = ydl.prepare_filename(ydl.extract_info(url))
        callback_query.message.reply_video(video=file_name)
        callback_query.answer("Downloading and sending your video!")
