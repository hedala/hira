import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# Video bilgilerini ve linklerini tutmak için bir dictionary
video_options = {}

# YT-DLP ile en iyi 4 videoyu bulma
def get_best_videos(youtube_url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = sorted(info['formats'], key=lambda x: x.get('height', 0), reverse=True)
        best_formats = formats[:4]
        
        video_data = []
        for f in best_formats:
            video_data.append({
                'url': f['url'],
                'format_id': f['format_id'],
                'ext': f['ext'],
                'height': f.get('height', 'unknown'),
                'width': f.get('width', 'unknown')
            })
    return video_data

@Client.on_message(filters.command("yt") & filters.private)
def yt_command(client, message):
    youtube_url = message.text.split()[1]
    best_videos = get_best_videos(youtube_url)
    
    # Kullanıcıya video seçeneklerini sunmak için butonları oluştur
    buttons = []
    for i, video in enumerate(best_videos):
        button_text = f"{video['height']}p"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"video_{i}")])
    
    video_options[message.from_user.id] = best_videos
    message.reply("Videoyu hangi kalitede indirmek istiyorsunuz?", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query()
def callback_query(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if user_id not in video_options:
        callback_query.answer("Videoyu indirme seçenekleri bulunamadı.", show_alert=True)
        return
    
    if data.startswith("video_"):
        index = int(data.split("_")[1])
        selected_video = video_options[user_id][index]
        
        # Video dosyasını indir
        ydl_opts = {
            'format': selected_video['format_id'],
            'outtmpl': f"{selected_video['format_id']}.{selected_video['ext']}"
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([callback_query.message.text.split()[1]])
        
        # Kullanıcıya videoyu gönder
        video_file = f"{selected_video['format_id']}.{selected_video['ext']}"
        client.send_video(user_id, video_file)
        
        # Geçici video dosyasını sil
        os.remove(video_file)
