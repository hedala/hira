from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os
import wget

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    video_file = None
    thumb = None
    try:
        link = message.command[1] if len(message.command) > 1 else None
        if not link:
            await message.reply_text("Lütfen bir YouTube linki sağlayın.", quote=True)
            return

        start_message = await message.reply_text("Video indiriliyor...", quote=True)

        for user_agent in user_agents:
            ydl_opts = {
                'format': 'bestvideo[height<=1080]+bestaudio/best',
                'merge_output_format': 'mp4',
                'writethumbnail': True,
                'postprocessors': [{'key': 'EmbedThumbnail'}, {'key': 'FFmpegMetadata'}],
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'user_agent': user_agent,
                'nocheckcertificate': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(link, download=True)
                    video_file = ydl.prepare_filename(info_dict)
                    title = info_dict.get('title')
                    thumbnails = info_dict.get("thumbnails", [])
                    jpg_thumbnails = [thumb for thumb in thumbnails if thumb['url'].endswith('.jpg')]

                    if jpg_thumbnails:
                        highest_thumbnail = max(jpg_thumbnails, key=lambda t: int(t['id']))
                        thumbnail_url = highest_thumbnail['url']
                        thumb = wget.download(thumbnail_url)
                break
            except Exception:
                continue

        await start_message.edit_text("Video başarıyla indirildi! Gönderiliyor...")

        await message.reply_video(
            video=video_file,
            caption=f"📹 Video: {title}",
            supports_streaming=True,
            thumb=thumb
        )

    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {str(e)}", quote=True)
    finally:
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
