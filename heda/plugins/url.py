import os
import subprocess
from pyrogram import Client, filters

def download_video(video_url):
    # yt-dlp komutunu çalıştır ve videoyu indir
    result = subprocess.run(['yt-dlp', '-f', 'best', video_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return None
    # İndirilen dosyanın adını al
    output = result.stdout.decode('utf-8')
    file_name = output.split("Destination: ")[-1].strip()
    return file_name

@Client.on_message(filters.command("url"))
def handle_url(client, message):
    if len(message.command) < 2:
        message.reply_text("Lütfen bir URL sağlayın.")
        return
    
    video_url = message.command[1]
    file_name = download_video(video_url)
    
    if not file_name:
        message.reply_text("Video indirilemedi.")
        return
    
    # Dosyayı kullanıcıya gönder
    message.reply_document(document=file_name)
    
    # Geçici dosyayı sil
    os.remove(file_name)
