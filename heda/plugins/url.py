import os
import json
import subprocess
from pyrogram import Client, filters
from aria2p import API, Client as Aria2Client


# Aria2 RPC bilgileri
ARIA2_RPC_HOST = "http://localhost"
ARIA2_RPC_PORT = 6800
ARIA2_RPC_SECRET = "HEDALA"

# Aria2 istemcisi
aria2 = API(
    Aria2Client(
        host=ARIA2_RPC_HOST,
        port=ARIA2_RPC_PORT,
        secret=ARIA2_RPC_SECRET
    )
)

def get_highest_quality_link(video_url):
    # youtube-dl komutunu çalıştır ve JSON çıktısını al
    result = subprocess.run(['youtube-dl', '-j', video_url], stdout=subprocess.PIPE)
    video_info = json.loads(result.stdout)
    
    # En yüksek kalitedeki formatı bul
    highest_quality_format = max(video_info['formats'], key=lambda x: x.get('quality', 0))
    
    return highest_quality_format['url']

@Client.on_message(filters.command("url"))
def download_video(client, message):
    if len(message.command) < 2:
        message.reply_text("Lütfen bir URL sağlayın.")
        return
    
    video_url = message.command[1]
    download_link = get_highest_quality_link(video_url)
    
    if not download_link:
        message.reply_text("İndirilebilir link bulunamadı.")
        return
    
    # Dosyayı indir
    download = aria2.add_uris([download_link])
    
    # İndirme işlemini takip et
    while not download.is_complete:
        download.update()
    
    # İndirilen dosyanın yolunu al
    file_path = download.files[0].path
    
    # Dosyayı kullanıcıya gönder
    message.reply_document(document=file_path)
    
    # Geçici dosyayı sil
    os.remove(file_path)
