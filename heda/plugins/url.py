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

    progress_message = await message.reply("Video indiriliyor, lütfen bekleyin...")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'progress_hooks': [progress_hook],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    async def send_progress_message():
        while not progress_data.get('completed', False):
            if 'percentage' in progress_data:
                try:
                    await progress_message.edit_text(
                        f"İndirme ilerlemesi: {progress_data['percentage']}, Hız: {progress_data['speed']}, Kalan süre: {progress_data['eta']}"
                    )
                except Exception as e:
                    print(f"Error updating progress message: {e}")
            await asyncio.sleep(4)

    progress_task = asyncio.create_task(send_progress_message())

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = ydl.prepare_filename(info_dict)
        progress_data['completed'] = True

    await progress_task

    await progress_message.edit_text("Video indirildi, yükleniyor...")

    async def upload_progress(current, total):
        if current == total:
            progress_data['upload_completed'] = True
        if 'upload_completed' not in progress_data:
            try:
                await progress_message.edit_text(f"Yükleme ilerlemesi: {current * 100 / total:.1f}%")
            except Exception as e:
                print(f"Error updating upload progress message: {e}")

    async def send_upload_progress_message():
        while not progress_data.get('upload_completed', False):
            await asyncio.sleep(5)

    upload_progress_task = asyncio.create_task(send_upload_progress_message())

    await client.send_video(
        chat_id=message.chat.id,
        video=video_title,
        caption="İşte videonuz!",
        progress=upload_progress
    )

    await upload_progress_task

    os.remove(video_title)
