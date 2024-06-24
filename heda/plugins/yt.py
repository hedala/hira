from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os

from heda import redis, log

@Client.on_message(filters.command(["yt"]))
async def handle_yt_command(_, message: Message):
    try:
        user_id = message.from_user.id
        link = message.command[1] if len(message.command) > 1 else None

        if not link:
            await message.reply_text(
                text="Lütfen bir YouTube linki sağlayın.",
                quote=True
            )
            return

        start_message = await message.reply_text(
            text="Video indiriliyor.. %0",
            quote=True
        )

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'progress_hooks': [lambda d: progress_hook(d, start_message)],
            'outtmpl': 'downloads/%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)

        await start_message.edit_text(
            text="Video başarıyla indirildi!"
        )

        await message.reply_video(
            video=video_file,
            caption="İşte indirdiğiniz video!"
        )

        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name}."
        )

        new_user = await redis.is_added(
            "NEW_USER", user_id
        )
        if not new_user:
            await redis.add_to_db(
                "NEW_USER", user_id
            )

        # İndirilen dosyayı temizleyelim
        if os.path.exists(video_file):
            os.remove(video_file)

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text(
            text=f"Bir hata oluştu: {str(e)}",
            quote=True
        )

def progress_hook(d, start_message):
    if d['status'] == 'downloading':
        percentage = d['_percent_str']
        text = f"Video indiriliyor.. %{percentage}"
        start_message.edit_text(text)
