import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

# İndirme ilerlemesini takip etmek için bir callback fonksiyonu
progress_data = {}

def progress_hook(d):
    if d['status'] == 'downloading':
        progress_data['percentage'] = d['_percent_str']
        progress_data['speed'] = d['_speed_str']
        progress_data['eta'] = d['_eta_str']

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
        'format': 'bestvideo+bestaudio/best',
        'progress_hooks': [progress_hook],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    async def send_progress_message():
        while not progress_data.get('completed', False):
            if 'percentage' in progress_data:
                await message.reply(f"İndirme ilerlemesi: {progress_data['percentage']}, Hız: {progress_data['speed']}, Kalan süre: {progress_data['eta']}")
            await asyncio.sleep(3)

    progress_task = asyncio.create_task(send_progress_message())

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = ydl.prepare_filename(info_dict)
        progress_data['completed'] = True

    await progress_task

    await message.reply("Video indirildi, yükleniyor...")

    async def upload_progress(current, total):
        await message.reply(f"Yükleme ilerlemesi: {current * 100 / total:.1f}%")

    await client.send_video(
        chat_id=message.chat.id,
        video=video_title,
        caption="İşte videonuz!",
        progress=upload_progress
    )

    os.remove(video_title)
