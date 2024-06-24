import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch

# YoutubeDL options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

@Client.on_message(filters.command("yt"))
async def youtube_command(client, message):
    command = message.text.split(maxsplit=1)
    if len(command) == 1:
        await message.reply("Please provide a YouTube link or search query.")
        return

    query = command[1]
    if "youtube.com" in query or "youtu.be" in query:
        await process_youtube_link(message, query)
    else:
        await search_youtube(message, query)

async def process_youtube_link(message, link):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Video 720p", callback_data=f"video_720p_{link}"),
         InlineKeyboardButton("Video 1080p", callback_data=f"video_1080p_{link}")],
        [InlineKeyboardButton("Video 2K", callback_data=f"video_2K_{link}"),
         InlineKeyboardButton("Video 4K", callback_data=f"video_4K_{link}")],
        [InlineKeyboardButton("Best Video", callback_data=f"video_best_{link}")],
        [InlineKeyboardButton("Audio MP3 128kbps", callback_data=f"audio_mp3_128_{link}"),
         InlineKeyboardButton("Audio MP3 320kbps", callback_data=f"audio_mp3_320_{link}")],
        [InlineKeyboardButton("Audio FLAC", callback_data=f"audio_flac_{link}"),
         InlineKeyboardButton("Best Audio", callback_data=f"audio_best_{link}")]
    ])
    await message.reply("Choose a format:", reply_markup=keyboard)

async def search_youtube(message, query):
    videos_search = VideosSearch(query, limit=5)
    results = videos_search.result()["result"]
    
    keyboard = []
    for video in results:
        keyboard.append([InlineKeyboardButton(video["title"], callback_data=f"search_{video['link']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply("Select a video:", reply_markup=reply_markup)

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data.split("_")
    if data[0] == "search":
        link = "_".join(data[1:])
        await process_youtube_link(callback_query.message, link)
    else:
        format_type, quality, link = data[0], data[1], "_".join(data[2:])
        await download_and_send(callback_query.message, link, format_type, quality)

async def download_and_send(message, link, format_type, quality):
    progress_message = await message.reply("Starting download...")
    
    if format_type == "video":
        ydl_opts['format'] = f'bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]' if quality != "best" else 'bestvideo+bestaudio/best'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        if quality == "mp3_128":
            ydl_opts['postprocessors'][0]['preferredquality'] = '128'
        elif quality == "mp3_320":
            ydl_opts['postprocessors'][0]['preferredquality'] = '320'
        elif quality == "flac":
            ydl_opts['postprocessors'][0]['preferredcodec'] = 'flac'
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d['_percent_str']
            speed = d['_speed_str']
            eta = d['_eta_str']
            asyncio.ensure_future(progress_message.edit(f"Downloading: {percent} | Speed: {speed} | ETA: {eta}"))

    ydl_opts['progress_hooks'] = [progress_hook]
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        filename = ydl.prepare_filename(info)
        ydl.download([link])
    
    await progress_message.delete()
    
    if format_type == "video":
        await message.reply_video(
            filename,
            caption=f"{info['title']} [{quality}]",
            duration=info['duration'],
            thumb=info['thumbnail']
        )
    else:
        await message.reply_audio(
            filename,
            caption=f"{info['title']} [{quality}]",
            duration=info['duration'],
            thumb=info['thumbnail']
        )
