import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp


# Video kalitesi seçenekleri
qualities = ["2160p", "1440p", "1080p", "720p"]

# Kalite butonlarını oluştur
def create_quality_buttons():
    buttons = []
    for quality in qualities:
        buttons.append([InlineKeyboardButton(quality, callback_data=quality)])
    return InlineKeyboardMarkup(buttons)

# Video bilgilerini al
def get_video_info(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        return formats

# En iyi kaliteyi bul
def find_best_quality(formats, desired_quality):
    for format in formats:
        if format.get('format_note') == desired_quality:
            return format
    return None

@Client.on_message(filters.command("yt") & filters.private)
async def yt_command(client, message):
    if len(message.command) < 2:
        await message.reply("Lütfen bir YouTube linki sağlayın.")
        return

    url = message.command[1]
    if not re.match(r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$', url):
        await message.reply("Geçersiz YouTube linki. Lütfen doğru bir link sağlayın.")
        return

    formats = get_video_info(url)
    if not formats:
        await message.reply("Video bilgileri alınamadı.")
        return

    await message.reply("Lütfen indirmek istediğiniz kaliteyi seçin:", reply_markup=create_quality_buttons())

@Client.on_callback_query(filters.regex(r'^(2160p|1440p|1080p|720p)$'))
async def callback_query_handler(client, callback_query):
    try:
        quality = callback_query.data
        url = callback_query.message.reply_to_message.command[1]
        formats = get_video_info(url)
        best_format = find_best_quality(formats, quality)

        if not best_format:
            await callback_query.message.reply("Seçilen kalite bulunamadı.")
            return

        ydl_opts = {
            'format': best_format['format_id'],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info_dict)

        await client.send_video(chat_id=callback_query.message.chat.id, video=file_path)
        await callback_query.message.reply("Video başarıyla indirildi ve gönderildi.")
    except Exception as e:
        await callback_query.message.reply(f"Bir hata oluştu: {str(e)}")
