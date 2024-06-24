from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os
import asyncio
import time

from heda import redis, log

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    try:
        user_id = message.from_user.id
        link = message.command[1] if len(message.command) > 1 else None

        if not link:
            await message.reply_text(
                text="Lütfen bir YouTube linki sağlayın.",
                quote=True
            )
            return

        start_message = await message.reply_text(
            text="Video bilgileri alınıyor...",
            quote=True
        )

        video_file = None  # Initialize video_file to None

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'merge_output_format': 'mp4',
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'EmbedThumbnail'},
            ],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'progress_hooks': [lambda d: asyncio.ensure_future(progress_hook(d, start_message))],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)
            duration = info_dict.get('duration')
            title = info_dict.get('title')
            channel = info_dict.get('channel')
            view_count = info_dict.get('view_count')
            upload_date = info_dict.get('upload_date')

        await start_message.edit_text("Video başarıyla indirildi! Gönderiliyor...")

        caption = (
            f"📹 Video: {title}\n"
            f"👤 Kanal: {channel}\n"
            f"👁️ Görüntülenme: {view_count:,}\n"
            f"📅 Yüklenme Tarihi: {upload_date}\n"
            f"⏱️ Süre: {duration // 60} dakika {duration % 60} saniye"
        )

        # Find the thumbnail file
        thumbnail_file = None
        for ext in ['.jpg', '.png', '.webp']:
            possible_thumb = video_file.rsplit(".", 1)[0] + ext
            if os.path.exists(possible_thumb):
                thumbnail_file = possible_thumb
                break

        try:
            await message.reply_video(
                video=video_file,
                caption=caption,
                supports_streaming=True,
                duration=duration,
                thumb=thumbnail_file
            )
        except Exception as e:
            log(__name__).error(f"Video gönderme hatası: {str(e)}")
            await message.reply_text(
                text="Video gönderilirken bir hata oluştu.",
                quote=True
            )

        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name}."
        )

        new_user = await redis.is_added(
            "NEW_USER", user_id
        )
        if not new_user:
            await redis.add_to_db(
                "NEW_USER", user_id
            )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text(
            text=f"Bir hata oluştu: {str(e)}",
            quote=True
        )
    finally:
        # İndirilen dosyaları temizleyelim
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)

last_update_time = 0
update_interval = 3  # seconds

async def progress_hook(d, start_message):
    global last_update_time
    current_time = time.time()
    
    if d['status'] == 'downloading':
        if current_time - last_update_time >= update_interval:
            percentage = d['_percent_str']
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            text = f"Video indiriliyor...\n📊 İlerleme: {percentage}\n🚀 Hız: {speed}\n⏳ Tahmini süre: {eta}"
            try:
                await start_message.edit_text(text)
                last_update_time = current_time
            except Exception as e:
                log(__name__).error(f"İlerleme güncellemesi hatası: {str(e)}")
    elif d['status'] == 'finished':
        await start_message.edit_text("Video indirildi. İşleniyor...")
