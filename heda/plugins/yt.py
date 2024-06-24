import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch

# İndirme işlemi sırasında ilerleme durumu için hook fonksiyonu
def progress_hook(d):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        app.send_message(chat_id=d['chat_id'], text=f"Video indiriliyor. %{percentage}")

# İndirme işlemi için yt-dlp seçenekleri
def get_ydl_opts(format_id, chat_id):
    return {
        'format': format_id,
        'progress_hooks': [progress_hook],
        'outtmpl': f'%(title)s_{format_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegMetadata',
        }],
        'logger': MyLogger(chat_id)
    }

class MyLogger:
    def __init__(self, chat_id):
        self.chat_id = chat_id

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        app.send_message(chat_id=self.chat_id, text=msg)

@Client.on_message(filters.command("yt"))
def yt_command(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) == 1:
        message.reply("Lütfen bir YouTube linki veya arama terimi girin.")
        return

    query = args[1]
    if query.startswith("http"):
        send_format_options(message, query)
    else:
        search_youtube(message, query)

def send_format_options(message, url):
    buttons = [
        [InlineKeyboardButton("Video", callback_data=f"video|{url}"), InlineKeyboardButton("Müzik", callback_data=f"audio|{url}")]
    ]
    message.reply("Hangi formatta indirmek istersiniz?", reply_markup=InlineKeyboardMarkup(buttons))

def search_youtube(message, query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    buttons = []
    for result in results:
        title = result['title']
        url = f"https://www.youtube.com{result['url_suffix']}"
        buttons.append([InlineKeyboardButton(title, callback_data=f"select|{url}")])
    message.reply("Arama sonuçları:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"select\|"))
def select_result(client, callback_query):
    url = callback_query.data.split("|")[1]
    send_format_options(callback_query.message, url)

@Client.on_callback_query(filters.regex(r"video\|"))
def video_options(client, callback_query):
    url = callback_query.data.split("|")[1]
    buttons = [
        [InlineKeyboardButton("720p", callback_data=f"download|{url}|bestvideo[height<=720]+bestaudio/best[height<=720]")],
        [InlineKeyboardButton("1080p", callback_data=f"download|{url}|bestvideo[height<=1080]+bestaudio/best[height<=1080]")],
        [InlineKeyboardButton("2K", callback_data=f"download|{url}|bestvideo[height<=1440]+bestaudio/best[height<=1440]")],
        [InlineKeyboardButton("4K", callback_data=f"download|{url}|bestvideo[height<=2160]+bestaudio/best[height<=2160]")],
        [InlineKeyboardButton("En İyi Kalite", callback_data=f"download|{url}|bestvideo+bestaudio/best")]
    ]
    callback_query.message.reply("Video kalitesini seçin:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"audio\|"))
def audio_options(client, callback_query):
    url = callback_query.data.split("|")[1]
    buttons = [
        [InlineKeyboardButton("MP3 128kbps", callback_data=f"download|{url}|bestaudio[ext=mp3]/best[ext=mp3]/bestaudio[abr<=128]")],
        [InlineKeyboardButton("MP3 320kbps", callback_data=f"download|{url}|bestaudio[ext=mp3]/best[ext=mp3]/bestaudio[abr<=320]")],
        [InlineKeyboardButton("FLAC", callback_data=f"download|{url}|bestaudio[ext=flac]/best[ext=flac]")],
        [InlineKeyboardButton("En İyi Kalite", callback_data=f"download|{url}|bestaudio/best")]
    ]
    callback_query.message.reply("Ses kalitesini seçin:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"download\|"))
def download_media(client, callback_query):
    _, url, format_id = callback_query.data.split("|")
    chat_id = callback_query.message.chat.id
    ydl_opts = get_ydl_opts(format_id, chat_id)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    callback_query.message.reply("İndirme tamamlandı!")
