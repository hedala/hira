from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp
from heda import redis, log

@Client.on_message(filters.command(["wh"]))
async def handle_weather_command(_, message: Message):
    try:
        city = message.text.split()[1]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://wttr.in/{city}?format=%C+%t+%w+%h&lang=tr") as response:
                if response.status == 200:
                    weather_data = await response.text()
                    weather_info = weather_data.split()
                    condition = weather_info[0]
                    temperature = weather_info[1]
                    wind = weather_info[2]
                    humidity = weather_info[3]
                    formatted_weather = (
                        f"{city} için hava durumu:\n"
                        f"Durum: {condition}\n"
                        f"Sıcaklık: {temperature}\n"
                        f"Rüzgar: {wind}\n"
                        f"Nem: {humidity}"
                    )
                else:
                    formatted_weather = "Hava durumu bilgisi alınamadı."
        
        await message.reply_text(
            text=formatted_weather,
            quote=True
        )

        log(__name__).info(
            f"/wh command was called by {message.from_user.full_name} for city {city}."
        )
    
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text(
            text="Bir hata oluştu. Lütfen tekrar deneyin.",
            quote=True
        )
