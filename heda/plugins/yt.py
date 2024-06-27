import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

@Client.on_message(filters.command("yt"))
async def youtube_downloader(client, message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a YouTube link.")
        return
    
    link = message.command[1]
    
    try:
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
            buttons.append([InlineKeyboardButton(f"{q}p", callback_data=f"download_{q}|{link}")])
        
        await message.reply_text(
            f"Video: {title}\nSelect the desired quality:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@Client.on_callback_query(filters.regex(r"^download_"))
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("|")
    quality = int(data[0].split("_")[1])
    link = data[1]
    
    try:
        download_message = await callback_query.message.reply_text("Download started. Please wait...")
        
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(link, download=False)
            title = info["title"]
        
        safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_file = f"{safe_title}_{quality}p.%(ext)s"
        
        ydl_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "outtmpl": output_file,
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        
        mp4_file = output_file.replace(".%(ext)s", ".mp4")
        webm_file = output_file.replace(".%(ext)s", ".webm")

        print(f"MP4 File Path: {mp4_file}")
        print(f"WEBM File Path: {webm_file}")

        if os.path.exists(mp4_file):
            print("MP4 file exists. Preparing to send...")
            await callback_query.message.reply_video(
                mp4_file,
                caption=f"Video downloaded in {quality}p quality."
            )
            os.remove(mp4_file)
            await download_message.edit_text("Download completed and video sent!")
        elif os.path.exists(webm_file):
            print("WEBM file exists. Preparing to send...")
            await callback_query.message.reply_video(
                webm_file,
                caption=f"Video downloaded in {quality}p quality."
            )
            os.remove(webm_file)
            await download_message.edit_text("Download completed and video sent!")
        else:
            await download_message.edit_text("Download completed, but file not found.")
            print("Download completed, but file not found.")
    
    except Exception as e:
        await callback_query.message.reply_text(f"An error occurred during download: {str(e)}")
        print(f"An error occurred during download: {str(e)}")
