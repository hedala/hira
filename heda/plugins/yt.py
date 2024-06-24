import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from threading import Thread

# Bot tokenını buraya girin
BOT_TOKEN = 'YOUR_BOT_TOKEN'

app = Client("my_bot", bot_token=BOT_TOKEN)

# İndirme işlemi sırasında ilerleme durumunu takip etmek için
progress_message = None

def download_video(youtube_link, format_code, chat_id, message_id):
    global progress_message
    ydl_opts = {
        'format': format_code,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [lambda d: on_progress(d, chat_id, message_id)]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])

def on_progress(d, chat_id, message_id):
    global progress_message
    if d['status'] == 'downloading':
        percent = d['_percent_str']
        if progress_message:
            asyncio.run(progress_message.edit_text(f"Video indiriliyor. {percent} tamamlandı."))
        else:
            progress_message = asyncio.run(app.send_message(chat_id, f"Video indiriliyor. {percent} tamamlandı.", reply_to_message_id=message_id))
    elif d['status'] == 'finished':
        asyncio.run(progress_message.delete())
        progress_message = None

@Client.on_message(filters.command("yt"))
async def yt_command(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Lütfen bir YouTube linki girin.")
        return

    youtube_link = args[1]
    buttons = [
        [InlineKeyboardButton("Video", callback_data=f"format:video:{youtube_link}"),
         InlineKeyboardButton("Audio", callback_data=f"format:audio:{youtube_link}")]
    ]
    await message.reply("Hangi formattan indirmek istersiniz?", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"format:(video|audio):(.*)"))
async def format_callback(client, callback_query):
    format_type, youtube_link = callback_query.data.split(":")[1:]
    format_list = get_formats(youtube_link, format_type)
    buttons = [[InlineKeyboardButton(fmt, callback_data=f"download:{fmt}:{youtube_link}")] for fmt in format_list]
    await callback_query.message.edit_text(f"Lütfen bir {format_type} kalitesi seçin:", reply_markup=InlineKeyboardMarkup(buttons))

def get_formats(youtube_link, format_type):
    ydl_opts = {'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_link, download=False)
        formats = []
        for fmt in info['formats']:
            if format_type == 'video' and fmt.get('vcodec') != 'none':
                formats.append(f"{fmt['format_id']} - {fmt['format_note']} - {fmt['ext']}")
            elif format_type == 'audio' and fmt.get('acodec') != 'none':
                formats.append(f"{fmt['format_id']} - {fmt['abr']}kbps - {fmt['ext']}")
        return formats

@Client.on_callback_query(filters.regex(r"download:(.*):(.*)"))
async def download_callback(client, callback_query):
    format_code, youtube_link = callback_query.data.split(":")[1:]
    await callback_query.message.edit_text("İndirme işlemi başlatılıyor...")

    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    download_thread = Thread(target=download_video, args=(youtube_link, format_code, chat_id, message_id))
    download_thread.start()

@Client.on_callback_query(filters.regex(r"send_video:(.*)"))
async def send_video_callback(client, callback_query):
    video_file = callback_query.data.split(":")[1]
    await client.send_video(callback_query.message.chat.id, video_file, supports_streaming=True)
    os.remove(video_file)
