from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp


# /yt komutu için handler
@Client.on_message(filters.command("yt"))
def yt_handler(client, message):
    query = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else None
    if not query:
        message.reply("Lütfen bir YouTube linki veya arama terimi girin.")
        return

    buttons = [
        [InlineKeyboardButton("Video İndir", callback_data=f"video|{query}")],
        [InlineKeyboardButton("Müzik İndir", callback_data=f"audio|{query}")]
    ]
    message.reply("İndirme formatını seçin:", reply_markup=InlineKeyboardMarkup(buttons))

# Butonlara tıklama için callback handler
@Client.on_callback_query(filters.regex(r"^(video|audio)\|"))
def callback_query_handler(client, callback_query):
    format_type, query = callback_query.data.split("|", 1)
    url = query if "http" in query else f"ytsearch:{query}"

    ydl_opts = {
        'format': 'bestaudio/best' if format_type == "audio" else 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format_type == "audio" else []
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [info_dict])
        buttons = [
            [InlineKeyboardButton(f"{f['format_id']} - {f['ext']} - {f['filesize'] // 1024 // 1024} MB", callback_data=f"download|{f['format_id']}|{query}")]
            for f in formats if f.get('filesize')
        ]
        callback_query.message.reply("Kalite seçin:", reply_markup=InlineKeyboardMarkup(buttons))

# İndirme işlemi için callback handler
@Client.on_callback_query(filters.regex(r"^download\|"))
def download_handler(client, callback_query):
    format_id, query = callback_query.data.split("|", 2)[1:]
    url = query if "http" in query else f"ytsearch:{query}"

    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        callback_query.message.reply("İndirme tamamlandı!")
                                                 
