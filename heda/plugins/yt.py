from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os

def download_video_quality(video_url, quality_format):
    ydl_opts = {
        'format': quality_format,
        'outtmpl': '%(title)s%(format_id)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def progress_hook(d):
    if d['status'] == 'downloading':
        progress = d['_percent_str']
        bot.send_message(d['filename'] + ' indiriliyor. ' + progress)

@Client.on_message(filters.command("yt", prefixes="/"))
def youtube_dl(bot, message):
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        search_query = text[1]
        if search_query.startswith("http"):
            video_url = search_query
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("720p", callback_data="720p"),
                        InlineKeyboardButton("1080p", callback_data="1080p"),
                        InlineKeyboardButton("2K", callback_data="2K"),
                        InlineKeyboardButton("4K", callback_data="4K"),
                        InlineKeyboardButton("Best Video", callback_data="best_video"),
                    ],
                    [
                        InlineKeyboardButton("MP3 128 kbps", callback_data="mp3_128"),
                        InlineKeyboardButton("MP3 320 kbps", callback_data="mp3_320"),
                        InlineKeyboardButton("FLAC", callback_data="flac"),
                        InlineKeyboardButton("Best Audio", callback_data="best_audio"),
                    ],
                ]
            )
            bot.send_message(message.chat.id, "Video formatını seçin:", reply_markup=keyboard)
        else:
            search_results = yt_dlp.YoutubeDL().extract_info(f"ytsearch5:{search_query}", download=False)
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(search_results['entries'][i]['title'], callback_data=f"result_{i}")
                    ] for i in range(5)
                ]
            )
            bot.send_message(message.chat.id, "Arama sonuçları:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Lütfen bir YouTube linki veya arama terimi girin.")

@Client.on_callback_query()
def callback_query(bot, update):
    data = update.data
    message = update.message
    if data.startswith("result_"):
        index = int(data.split("_")[1])
        video_url = message.reply_markup.inline_keyboard[index][0].url
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("720p", callback_data="720p"),
                    InlineKeyboardButton("1080p", callback_data="1080p"),
                    InlineKeyboardButton("2K", callback_data="2K"),
                    InlineKeyboardButton("4K", callback_data="4K"),
                    InlineKeyboardButton("Best Video", callback_data="best_video"),
                ],
                [
                    InlineKeyboardButton("MP3 128 kbps", callback_data="mp3_128"),
                    InlineKeyboardButton("MP3 320 kbps", callback_data="mp3_320"),
                    InlineKeyboardButton("FLAC", callback_data="flac"),
                    InlineKeyboardButton("Best Audio", callback_data="best_audio"),
                ],
            ]
        )
        bot.send_message(message.chat.id, "Video formatını seçin:", reply_markup=keyboard)
        bot.answer_callback_query(update.id)
    else:
        if data.startswith("720p"):
            quality_format = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif data.startswith("1080p"):
            quality_format = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif data.startswith("2K"):
            quality_format = 'bestvideo[height<=1440]+bestaudio/best[height<=1440]'
        elif data.startswith("4K"):
            quality_format = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
        elif data.startswith("best_video"):
            quality_format = 'bestvideo+bestaudio/best'
        elif data.startswith("mp3_128"):
            quality_format = 'bestaudio/best'
        elif data.startswith("mp3_320"):
            quality_format = 'bestaudio/best'
        elif data.startswith("flac"):
            quality_format = 'bestaudio/best'
        elif data.startswith("best_audio"):
            quality_format = 'bestaudio/best'
        
        download_video_quality(video_url, quality_format)
        bot.answer_callback_query(update.id, "İndirme tamamlandı.")
