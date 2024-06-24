from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import subprocess

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
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'merge_output_format': 'mp4',
            'progress_hooks': [lambda d: progress_hook(d, start_message)],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)
            thumbnail_url = info_dict.get('thumbnail')
            duration = info_dict.get('duration')

        # Thumbnail'i indir
        thumbnail_file = None
        if thumbnail_url:
            thumbnail_response = requests.get(thumbnail_url)
            thumbnail_file = f"downloads/{info_dict['id']}.jpg"
            with open(thumbnail_file, 'wb') as f:
                f.write(thumbnail_response.content)

        # Pillow ile thumbnail ve süre bilgisi ekle
        if thumbnail_file:
            base = Image.open(thumbnail_file).convert('RGBA')
            txt = Image.new('RGBA', base.size, (255, 255, 255, 0))

            # Font ve yazı ayarları
            fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
            d = ImageDraw.Draw(txt)

            # Süre bilgisini ekle
            duration_text = f"{duration // 60} dakika {duration % 60} saniye"
            d.text((10, base.size[1] - 50), duration_text, font=fnt, fill=(255, 255, 255, 255))

            # Thumbnail'i ekle
            out = Image.alpha_composite(base, txt)
            thumbnail_with_text = f"downloads/{info_dict['id']}_thumb.png"
            out.save(thumbnail_with_text)

        # ffmpeg ile videoya thumbnail ve süre bilgisi ekle
        output_file = f"downloads/{info_dict['id']}_final.mp4"
        ffmpeg_command = [
            'ffmpeg', '-i', video_file, '-i', thumbnail_with_text, '-filter_complex',
            "[1:v]scale=320:240[thumb];[0:v][thumb]overlay=W-w-10:H-h-10",
            '-codec:a', 'copy', output_file
        ]
        subprocess.run(ffmpeg_command, check=True)

        await start_message.edit_text(
            text="Video başarıyla indirildi!"
        )

        caption = f"İşte indirdiğiniz video!\nSüre: {duration // 60} dakika {duration % 60} saniye"

        await message.reply_video(
            video=output_file,
            caption=caption
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

        # İndirilen dosyaları temizleyelim
        if os.path.exists(video_file):
            os.remove(video_file)
        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)
        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(thumbnail_with_text):
            os.remove(thumbnail_with_text)

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
