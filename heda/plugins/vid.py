import os
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

# Yüksek kalitede video indirme fonksiyonu
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s'
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info_dict)
    return video_file

@Client.on_message(filters.command("vid") & filters.private)
async def vid(client, message):
    if len(message.command) < 2:
        await message.reply_text("Lütfen bir YouTube linki sağlayın.")
        return

    url = message.command[1]
    await message.reply_text("Video indiriliyor, lütfen bekleyin...")

    try:
        video_file = download_video(url)
        await message.reply_video(video_file)
        os.remove(video_file)  # İndirilen dosyayı sil
    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {e}")
