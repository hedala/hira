import os
import time
import wget
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from heda import log  # Hata günlüğü için log fonksiyonunu import ediyoruz

@Client.on_message(filters.command(["you"]))
async def youtube_downloader(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("Lütfen bir YouTube bağlantısı sağlayın.")
            return
        link = message.command[1]
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(link, download=False)
            title = info["title"]
            formats = info["formats"]

        qualities = [2160, 1440, 1080, 720, 480, 360]
        available_qualities = []
        for q in qualities:
            for f in formats:
                if f.get("height") == q:
                    available_qualities.append(q)
                    break
        
        if not available_qualities:
            await message.reply_text("Uygun video formatı bulunamadı.")
            return
        
        buttons = []
        for q in available_qualities:
            buttons.append([InlineKeyboardButton(f"{q}p", callback_data=f"download_{q}")])
        await message.reply_text(
            f"Video: {title}\nİstediğiniz kaliteyi seçin:",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    except Exception as e:
        log(__name__).error(f"YouTube indirme hatası: {str(e)}")
        await message.reply_text("Video bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

@Client.on_callback_query(filters.regex("download_(360|480|720|1080|1440|2160)"))
async def callback_query_handler(client, callback_query):
    try:
        quality = int(callback_query.data.split("_")[1])
        link = callback_query.message.reply_to_message.text.split(" ", maxsplit=1)[1]
        
        download_message = await callback_query.message.edit_text("İndirme başladı. Lütfen bekleyin...")
        start_time = time.time()
        
        ydl_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "merge_output_format": "mp4",
            "outtmpl": "downloads/%(title)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            output_file = ydl.prepare_filename(info_dict)
            duration = info_dict.get("duration")
            thumbnails = info_dict.get("thumbnails", [])
            jpg_thumbnails = [t for t in thumbnails if t["url"].endswith(".jpg")]
            thumb_url = jpg_thumbnails[-1]["url"] if jpg_thumbnails else None
        
        if thumb_url:
            thumb = wget.download(thumb_url)
        else:
            thumb = None

        await download_message.edit_text("İndirme tamamlandı. Video gönderiliyor...")
        await callback_query.message.reply_video(
            video=output_file,
            caption=f"Video {quality}p kalitesinde indirildi.",
            duration=duration,
            thumb=thumb
        )

        await download_message.delete()
        if os.path.exists(output_file):
            os.remove(output_file)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
    except Exception as e:
        log(__name__).error(f"Video indirme ve gönderme hatası: {str(e)}")
        await callback_query.message.reply_text("Video indirilirken veya gönderilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
        
