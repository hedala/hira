from pyrogram import Client, filters
import speedtest
import asyncio

@Client.on_message(filters.command("dl"))
async def speedtest_command(client, message):
    speed = speedtest.Speedtest()
    download_speed = await asyncio.get_event_loop().run_in_executor(None, speed.download)
    upload_speed = await asyncio.get_event_loop().run_in_executor(None, speed.upload)
    await message.reply_text(f"İndirme Hızı: {download_speed / 1024 / 1024:.2f} Mbps\nYükleme Hızı: {upload_speed / 1024 / 1024:.2f} Mbps")
