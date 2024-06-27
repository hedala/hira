import os
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

# İndirme ilerlemesini takip etmek için bir callback fonksiyonu
def progress_hook(d):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        print(f"İndirme ilerlemesi: {percentage}")

@Client.on_message(filters.command("url") & filters.private)
async def download_video(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Lütfen bir link sağlayın.")
        return

    url = message.command[1]
    if "youtube.com" not in url and "ok.ru" not in url:
        await message.reply("Sadece YouTube ve ok.ru linkleri desteklenmektedir.")
        return

    await message.reply("Video indiriliyor, lütfen bekleyin...")

    ydl_opts = {
        'format': 'best',
        'progress_hooks': [progress_hook],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = ydl.prepare_filename(info_dict)

    await message.reply("Video indirildi, yükleniyor...")

    await client.send_video(
        chat_id=message.chat.id,
        video=video_title,
        caption="İşte videonuz!"
    )

    os.remove(video_title)
