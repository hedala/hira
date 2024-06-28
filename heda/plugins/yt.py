import os
import time
import wget
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Hata ayıklama için logging ekleyelim
import logging
logging.basicConfig(level=logging.INFO)

# İndirilen dosyaların kaydedileceği klasör
DOWNLOAD_DIR = "downloads"

# Klasörün mevcut olup olmadığını kontrol edelim, yoksa oluşturalım
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@Client.on_message(filters.command(["yt"]))
async def youtube_downloader(client, message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a YouTube link.")
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
        await message.reply_text("No suitable video formats found.")
        return
    
    buttons = []
    for q in available_qualities:
        buttons.append([InlineKeyboardButton(f"{q}p", callback_data=f"yt_download_{q}_{link}")])
    await message.reply_text(
        f"Video: {title}\nSelect the desired quality:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

@Client.on_callback_query(filters.regex("^yt_download_"))
async def callback_query_handler(client, callback_query):
    logging.info(f"Callback query received: {callback_query.data}")
    try:
        _, quality, link = callback_query.data.split("_", 2)
        quality = int(quality)
        
        download_message = await callback_query.message.edit_text("Download started. Please wait...")
        start_time = time.time()
        
        ydl_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            output_file = ydl.prepare_filename(info_dict)
            duration = info_dict.get("duration")
            thumbnails = info_dict.get("thumbnails", [])
            jpg_thumbnails = [t for t in thumbnails if t["url"].endswith(".jpg")][-1]["url"]
            logging.info(f"Thumbnail URL: {jpg_thumbnails}")
        
        thumb = wget.download(jpg_thumbnails, out=DOWNLOAD_DIR)
        await download_message.edit_text("Download completed. Video is being sent...")
        await callback_query.message.reply_video(
            video=output_file,
            caption=f"Video downloaded in {quality}p quality.",
            duration=duration,
            thumb=thumb
        )

        await download_message.delete()
        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(thumb):
            os.remove(thumb)
    except Exception as e:
        logging.error(f"Error in callback query handler: {str(e)}")
        await callback_query.message.reply_text(f"An error occurred: {str(e)}")
        
