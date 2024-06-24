import yt_dlp
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image

from heda import redis, log

def get_best_thumbnail(info_dict):
    """En kaliteli thumbnail URL'sini döndürür."""
    thumbnails = info_dict.get('thumbnails', [])
    best_thumbnail = max(thumbnails, key=lambda x: x['width'] * x['height'])
    return best_thumbnail['url']

async def embed_thumbnail(video_file, thumbnail_file):
    """Videoya thumbnail ekler."""
    cmd = f'ffmpeg -i "{video_file}" -i "{thumbnail_file}" -map 0 -map 1 -c copy -c:v copy -c:a copy -metadata:s:v:0 title="Album cover" -metadata:s:v:0 comment="Cover (front)" "{video_file}_with_thumb.mp4"'
    os.system(cmd)
    os.rename(f"{video_file}_with_thumb.mp4", video_file)

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

        # Farklı User-Agentler
        user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Mobile Safari/537.36',
            # Ekleyebileceğiniz daha fazla User-Agent...
        ]

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

                thumbnail_url = get_best_thumbnail(info_dict)

                await start_message.edit_text("Video başarıyla indirildi Gönderiliyor...")

                caption = (
                    f"📹 Video: {title}\n"
                    f"👤 Kanal: {channel}\n"
                    f"👁️ Görüntülenme: {view_count:,}\n"
                    f"📅 Yüklenme Tarihi: {upload_date}\n"
                    f"⏱️ Süre: {duration // 60} dakika {duration % 60} saniye"
                )

                thumbnail_file = 'downloads/thumbnail.jpg'
                os.system(f"wget -O {thumbnail_file} {thumbnail_url}")

                # Thumbnail dosyasının uzantısını kontrol et ve dönüştür
                if thumbnail_file.endswith(".webp"):
                    jpg_thumbnail = thumbnail_file.replace(".webp", ".jpg")
                    image = Image.open(thumbnail_file)
                    image.save(jpg_thumbnail, "JPEG")
                    thumbnail_file = jpg_thumbnail

                # Videoya thumbnail ekleyin
                await embed_thumbnail(video_file, thumbnail_file)

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
                    continue  # Bu User-Agent ile başarısız oldu, bir sonraki için devam et

                break  # Başarılı indirme, döngüyü sonlandır

            except yt_dlp.DownloadError as e:
                log(__name__).error(f"Video indirme hatası: {str(e)}")
                continue  # Bu User-Agent ile başarısız oldu, bir sonraki için devam et

        if video_file is None:
            await message.reply_text(
                text="Tüm User-Agentler ile video indirme işlemi başarısız oldu.",
                quote=True
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
                    
