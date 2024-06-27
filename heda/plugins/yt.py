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
    
    # Extract video info using yt-dlp
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(link, download=False)
        title = info["title"]
        formats = info["formats"]
    
    # Filter available qualities
    qualities = [2160, 1440, 1080, 720]
    available_qualities = []
    for q in qualities:
        for f in formats:
            if "height" in f and f["height"] == q:
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

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    if callback_query.data.startswith("download_"):
        quality = int(callback_query.data.split("_")[1])
        link = callback_query.message.reply_to_message.text.split(" ", maxsplit=1)[1]
        
        # Download video using yt-dlp
        output_file = f"{callback_query.message.chat.id}_{quality}.mp4"
        ydl_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "outtmpl": output_file,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        
        # Send downloaded video to the user
        await client.send_video(
            callback_query.message.chat.id,
            output_file,
            caption=f"Video downloaded in {quality}p quality."
        )
        
        # Clean up the downloaded file
        os.remove(output_file)
