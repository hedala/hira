import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

@Client.on_message(
    filters.command(["yt"])
    #& filters.user(5646751940)
)
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
            buttons.append([InlineKeyboardButton(f"{q}p", callback_data=f"download_{q}")])
        await message.reply_text(
            f"Video: {title}\nSelect the desired quality:",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")


@Client.on_callback_query(
    filters.regex("download_(360|480|720|1080|1440|2160)")
)
async def callback_query_handler(client, callback_query):
        quality = int(callback_query.data.split("_")[1])
        link = callback_query.message.reply_to_message.text.split(" ", maxsplit=1)[1]
        
        try:
            download_message = await callback_query.message.edit_text("Download started. Please wait...")
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
                'merge_output_format': 'mp4',
                "outtmpl": "downloads/%(title)s.%(ext)s",
                #"progress_hooks": [progress_hook],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(link, download=True)
                output_file = ydl.prepare_filename(info_dict)
            await download_message.edit_text("Download completed. Video is being sent...")
            await callback_query.message.reply_video(
                output_file,
                caption=f"Video downloaded in {quality}p quality."
            )
        except Exception as e:
            await callback_query.message.reply_text(f"An error occurred during download: {str(e)}")
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
