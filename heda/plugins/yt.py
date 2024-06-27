import os
import time
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
        # Extract video info using yt-dlp
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(link, download=False)
            title = info["title"]
            formats = info["formats"]
        
        # Filter available qualities
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
        
        # Create inline buttons for quality selection
        buttons = []
        for q in available_qualities:
            buttons.append([InlineKeyboardButton(f"{q}p", callback_data=f"download_{q}")])
        
        # Send message with quality selection buttons
        await message.reply_text(
            f"Video: {title}\nSelect the desired quality:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    if callback_query.data.startswith("download_"):
        quality = int(callback_query.data.split("_")[1])
        link = callback_query.message.reply_to_message.text.split(" ", maxsplit=1)[1]
        
        try:
            # Send download started message
            download_message = await callback_query.message.reply_text("Download started. Please wait...")
            
            # Download video using yt-dlp with progress updates
            output_file = f"{callback_query.message.chat.id}_{quality}.mp4"
            start_time = time.time()
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    downloaded_bytes = d.get("downloaded_bytes", 0)
                    total_bytes = d.get("total_bytes_estimate", 0)
                    elapsed_time = time.time() - start_time
                    
                    if total_bytes > 0:
                        progress = downloaded_bytes / total_bytes * 100
                        remaining_time = (total_bytes - downloaded_bytes) / (downloaded_bytes / elapsed_time)
                        progress_message = f"Downloading... {progress:.2f}% complete\n" \
                                           f"Time remaining: {remaining_time:.2f} seconds"
                    else:
                        progress_message = f"Downloading... {downloaded_bytes} bytes"
                    
                    client.loop.create_task(download_message.edit_text(progress_message))
            
            ydl_opts = {
                "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
                "outtmpl": output_file,
                "progress_hooks": [progress_hook],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            
            # Send downloaded video to the user
            await callback_query.message.reply_video(
                output_file,
                caption=f"Video downloaded in {quality}p quality."
            )
            
            # Clean up the downloaded file
            os.remove(output_file)
            
            # Edit download message to indicate completion
            await download_message.edit_text("Download completed and video sent!")
        
        except Exception as e:
            await callback_query.message.reply_text(f"An error occurred during download: {str(e)}")
