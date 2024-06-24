import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from threading import Thread

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
        await message.reply("Lütfen bir YouTube linki veya arama terimi girin.")
        return

    query = args[1]
    if query.startswith("http"):
        youtube_link = query
        buttons = [
            [InlineKeyboardButton("Video", callback_data=f"format:video:{youtube_link}"),
             InlineKeyboardButton("Audio", callback_data=f"format:audio:{youtube_link}")]
        ]
        await message.reply("Hangi formattan indirmek istersiniz?", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        search_results = search_youtube(query)
        buttons = [[InlineKeyboardButton(result['title'], callback_data=f"search:{result['id']}")] for result in search_results]
        await message.reply("Arama sonuçları:", reply_markup=InlineKeyboardMarkup(buttons))

def search_youtube(query):
    ydl_opts = {'default_search': 'ytsearch5', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return [{'id': entry['id'], 'title': entry['title']} for entry in info['entries']]

@Client.on_callback_query(filters.regex(r"search:(.*)"))
async def search_callback(client, callback_query):
    video_id = callback_query.data.split(":")[1]
    youtube_link = f"https://www.youtube.com/watch?v={video_id}"
    buttons = [
        [InlineKeyboardButton("Video", callback_data=f"format:video:{youtube_link}"),
         InlineKeyboardButton("Audio", callback_data=f"format:audio:{youtube_link}")]
    ]
    await callback_query.message.edit_text("Hangi formattan indirmek istersiniz?", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"format:(video|audio):(.*)"))
async def format_callback(client, callback_query):
    format_type, youtube_link = callback_query.data.split(":")[1:]
    format_list = get_best_formats(youtube_link, format_type)
    buttons = [[InlineKeyboardButton(fmt['label'], callback_data=f"download:{fmt['id']}:{youtube_link}")] for fmt in format_list]
    await callback_query.message.edit_text(f"Lütfen bir {format_type} kalitesi seçin:", reply_markup=InlineKeyboardMarkup(buttons))

def get_best_formats(youtube_link, format_type):
    ydl_opts = {'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_link, download=False)
        formats = []
        if format_type == 'video':
            desired_resolutions = ['1280x720', '1920x1080', '2560x1440', '3840x2160']
            for res in desired_resolutions:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' and fmt.get('resolution') == res:
                        formats.append({'id': fmt['format_id'], 'label': res})
                        break
        elif format_type == 'audio':
            audio_formats = sorted([fmt for fmt in info['formats'] if fmt.get('acodec') != 'none'], key=lambda x: x.get('abr', 0), reverse=True)
            for fmt in audio_formats[:4]:
                formats.append({'id': fmt['format_id'], 'label': f"{fmt['abr']}kbps"})
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
    
