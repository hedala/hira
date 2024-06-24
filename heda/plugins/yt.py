from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
import os
import asyncio

from heda import redis, log

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    link = message.command[1] if len(message.command) > 1 else None

    if not link:
        await message.reply_text(
            text="Lütfen bir YouTube linki sağlayın.",
            quote=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Video", callback_data=f"yt_video|{link}")],
            [InlineKeyboardButton("Audio", callback_data=f"yt_audio|{link}")]
        ]
    )

    await message.reply_text(
        text="Lütfen indirme formatını seçin:",
        reply_markup=keyboard,
        quote=True
    )

@Client.on_callback_query(filters.regex(r"yt_(video|audio)\|(.+)"))
async def handle_yt_callback(_, callback_query: CallbackQuery):
    format_type, link = callback_query.data.split("|")
    video_file = None
    thumbnail_file = None
    try:
        user_id = callback_query.from_user.id

        start_message = await callback_query.message.reply_text(
            text="İndirme işlemi başlatılıyor...",
            quote=True
        )

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best' if format_type == 'yt_video' else 'bestaudio/best',
            'merge_output_format': 'mp4' if format_type == 'yt_video' else 'mp3',
            'writethumbnail': format_type == 'yt_video',
            'postprocessors': [
                {'key': 'EmbedThumbnail'} if format_type == 'yt_video' else {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
            ],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)
            duration = info_dict.get('duration')
            title = info_dict.get('title')
            channel = info_dict.get('channel')
            view_count = info_dict.get('view_count')
            upload_date = info_dict.get('upload_date')

        await start_message.edit_text("İndirme tamamlandı! Gönderiliyor...")

        caption = (
            f"📹 Video: {title}\n"
            f"👤 Kanal: {channel}\n"
            f"👁️ Görüntülenme: {view_count:,}\n"
            f"📅 Yüklenme Tarihi: {upload_date}\n"
            f"⏱️ Süre: {duration // 60} dakika {duration % 60} saniye"
        )

        if format_type == 'yt_video':
            thumbnail_file = video_file.rsplit(".", 1)[0] + ".webp"
            if not os.path.exists(thumbnail_file):
                thumbnail_url = info_dict.get('thumbnail')
                if thumbnail_url:
                    thumbnail_file = 'downloads/thumbnail.jpg'
                    os.system(f"wget -O {thumbnail_file} {thumbnail_url}")

            await callback_query.message.reply_video(
                video=video_file,
                caption=caption,
                supports_streaming=True,
                duration=duration,
                thumb=thumbnail_file
            )
        else:
            await callback_query.message.reply_audio(
                audio=video_file,
                caption=caption,
                duration=duration
            )

        log(__name__).info(
            f"{callback_query.data} command was called by {callback_query.from_user.full_name}."
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
        await callback_query.message.reply_text(
            text=f"Bir hata oluştu: {str(e)}",
            quote=True
        )
    finally:
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)
            
