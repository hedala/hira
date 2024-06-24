from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os
import traceback
from PIL import Image
import wget
from heda import redis, log

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
]

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

        for user_agent in user_agents:
            ydl_opts = {
                'format': 'bestvideo[height<=1080]+bestaudio/best',
                'merge_output_format': 'mp4',
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'EmbedThumbnail'},
                    {'key': 'FFmpegMetadata'},
                ],
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'user_agent': user_agent,
                'nocheckcertificate': True,
                'cookiefile': 'cookies.txt',
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(link, download=True)
                    video_file = ydl.prepare_filename(info_dict)
                    duration = info_dict.get('duration')
                    title = info_dict.get('title')
                    channel = info_dict.get('channel')
                    view_count = info_dict.get('view_count')
                    upload_date = info_dict.get('upload_date')
                    thumbnails = info_dict.get("thumbnails", [])
                    jpg_thumbnails = [thumb for thumb in thumbnails if thumb['url'].endswith('.jpg')]

                    thumb = None
                    if jpg_thumbnails:
                        highest_thumbnail = max(jpg_thumbnails, key=lambda t: int(t['id']))
                        thumbnail_url = highest_thumbnail['url']
                        thumb = wget.download(thumbnail_url)
                break  # Başarılı olursa döngüyü kır
            except Exception as e:
                log(__name__).error(f"User-agent {user_agent} ile hata oluştu: {str(e)}")
                continue  # Hata olursa bir sonraki user-agent'a geç

        await start_message.edit_text("Video başarıyla indirildi! Gönderiliyor...")

        caption = (
            f"📹 Video: {title}\n"
            f"👤 Kanal: {channel}\n"
            f"👁️ Görüntülenme: {view_count:,}\n"
            f"📅 Yüklenme Tarihi: {upload_date}\n"
            f"⏱️ Süre: {duration // 60} dakika {duration % 60} saniye"
        )

        try:
            await message.reply_video(
                video=video_file,
                caption=caption,
                supports_streaming=True,
                duration=duration,
                thumb=thumb
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
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
                
