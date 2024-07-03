from pyrogram import Client, filters
import speedtest

@Client.on_message(filters.command("hız"))
def speedtest_command(client, message):
    speed = speedtest.Speedtest()
    download_speed = speed.download()
    upload_speed = speed.upload()
    message.reply_text(f"İndirme Hızı: {download_speed / 1024 / 1024:.2f} Mbps\nYükleme Hızı: {upload_speed / 1024 / 1024:.2f} Mbps")
