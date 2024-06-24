from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import wget

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

quality_options = {
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best",
    "1440p": "bestvideo[height<=1440]+bestaudio/best",
    "2160p": "bestvideo[height<=2160]+bestaudio/best"
}

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    link = message.command[1] if len(message.command) > 1 else None
    if not link:
        await message.reply_text("Lütfen bir YouTube linki sağlayın.", quote=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("720p", callback_data=f"yt_dl|720p|{link}")],
        [InlineKeyboardButton("1080p", callback_data=f"yt_dl|1080p|{link}")],
        [InlineKeyboardButton("1440p", callback_data=f"yt_dl|1440p|{link}")],
        [InlineKeyboardButton("2160p", callback_data=f"yt_dl|2160p|{link}")]
    ])

    await message.reply_text("Lütfen indirmek istediğiniz kaliteyi seçin:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"yt_dl\|"))
async def handle_quality_selection(client, callback_query):
    _, quality, link = callback_query.data.split("|")
    video_file = None
    thumb = None
    try:
        await callback_query.message.edit_text("Video indiriliyor...")

        for user_agent in user_agents:
            ydl_opts = {
                'format': quality_options[quality],
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
                    duration = info_dict.get('duration')
                    thumbnails = info_dict.get("thumbnails", [])
                    jpg_thumbnails = [thumb for thumb in thumbnails if thumb['url'].endswith('.jpg')]

                    if jpg_thumbnails:
                        highest_thumbnail = max(jpg_thumbnails, key=lambda t: int(t['id']))
                        thumbnail_url = highest_thumbnail['url']
                        thumb = wget.download(thumbnail_url)
                break
            except Exception:
                continue

        await callback_query.message.edit_text("Video başarıyla indirildi! Gönderiliyor...")

        await client.send_video(
            chat_id=callback_query.message.chat.id,
            video=video_file,
            caption=f"📹 Video: {title}",
            supports_streaming=True,
            duration=duration,
            thumb=thumb
        )

    except Exception as e:
        await callback_query.message.edit_text(f"Bir hata oluştu: {str(e)}")
    finally:
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
    
