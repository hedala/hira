import requests
from pyrogram import Client, filters


# Function to download video from URL
def download_video(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

# Handler for the /url command
@Client.on_message(filters.command("url") & filters.private)
def send_video(client, message):
    if len(message.command) == 2:
        url = message.command[1]
        file_name = "downloaded_video.mp4"
        
        # Download the video
        message.reply_text("Video indiriliyor...")
        download_video(url, file_name)
        
        # Send the video
        message.reply_text("Video gönderiliyor...")
        client.send_video(chat_id=message.chat.id, video=file_name)
    else:
        message.reply_text("Lütfen bir URL sağlayın: /url <link>")
