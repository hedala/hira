from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os
import asyncio
from PIL import Image

from heda import redis, log

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    video_file = None
    thumbnail_file = None
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
            text="Video indiriliyor...",
            quote=True
        )

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'merge_output_format': 'mp4',
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata'},
            ],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)
            duration = info_dict.get('duration')
            title = info_dict.get('title')
            channel = info_dict.get('channel')
            view_count = info_dict.get('view_count')
            upload_date = info_dict.get('upload_date')

            # En kaliteli thumbnail URL'sini al
            thumbnail_url = info_dict.get('thumbnails', [])[-1]['url']

        await start_message.edit_text("Video başarıyla indirildi! Gönderiliyor...")

        caption = (
            f"📹 Video: {title}\n"
            f"👤 Kanal: {channel}\n"
            f"👁️ Görüntülenme: {view_count:,}\n"
            f"📅 Yüklenme Tarihi: {upload_date}\n"
            f"⏱️ Süre: {duration // 60} dakika {duration % 60} saniye"
        )

        # Thumbnail dosyasını indir
        thumbnail_file = 'downloads/thumbnail.webp'
        os.system(f"wget -O {thumbnail_file} {thumbnail_url}")

        # Thumbnail dosyasının uzantısını kontrol et
        if thumbnail_file.endswith(".webp"):
            # .webp dosyasını .jpg formatına dönüştür
            jpg_thumbnail = thumbnail_file.replace(".webp", ".jpg")
            image = Image.open(thumbnail_file)
            image.save(jpg_thumbnail, "JPEG")
            thumbnail_file = jpg_thumbnail

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
            
