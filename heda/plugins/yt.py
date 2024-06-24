from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
import os
import wget

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

quality_options = {
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
}

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(client: Client, message: Message):
    link = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None
    if not link:
        await message.reply_text("Lütfen bir YouTube linki sağlayın.", quote=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("720p", callback_data=f"720p_{link}")],
        [InlineKeyboardButton("1080p", callback_data=f"1080p_{link}")],
        [InlineKeyboardButton("1440p", callback_data=f"1440p_{link}")],
        [InlineKeyboardButton("2160p", callback_data=f"2160p_{link}")]
    ])

    await message.reply_text("Lütfen indirmek istediğiniz kaliteyi seçin:", reply_markup=keyboard)

@Client.on_callback_query()
async def handle_quality_selection(client: Client, callback_query: CallbackQuery):
    try:
        quality, link = callback_query.data.split("_", 1)
        await callback_query.answer(f"Seçilen kalite: {quality}")
        await callback_query.message.edit_text(f"Video indiriliyor... Kalite: {quality}")

        video_file, thumb, title, duration = await download_video(link, quality)

        if video_file:
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=video_file,
                caption=f"📹 Video: {title}",
                supports_streaming=True,
                duration=duration,
                thumb=thumb
            )
            await callback_query.message.delete()
        else:
            await callback_query.message.edit_text("Video indirilemedi.")

    except Exception as e:
        await callback_query.message.edit_text(f"Bir hata oluştu: {str(e)}")
    finally:
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

async def download_video(link, quality):
    video_file = None
    thumb = None
    title = "Unknown Title"
    duration = None

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
                title = info_dict.get('title', 'Unknown Title')
                duration = info_dict.get('duration')
                thumbnails = info_dict.get("thumbnails", [])
                jpg_thumbnails = [t for t in thumbnails if t['url'].endswith('.jpg')]

                if jpg_thumbnails:
                    highest_thumbnail = max(jpg_thumbnails, key=lambda t: int(t.get('height', 0)))
                    thumbnail_url = highest_thumbnail['url']
                    thumb = wget.download(thumbnail_url)
            break
        except Exception as e:
            print(f"Error with user agent {user_agent}: {str(e)}")
            continue

    if not video_file:
        raise Exception("Video indirilemedi.")

    return video_file, thumb, title, duration
