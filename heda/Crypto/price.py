from pyrogram import Client, filters, enums
import aiohttp
from datetime import datetime
import pytz

from heda import redis, log

# Binance Futures API URL
BINANCE_FUTURES_API_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol="

def format_large_number(num):
    """
    Büyük sayıları M (milyon) veya B (milyar) olarak formatlar.
    """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    else:
        return f"{num:.2f}"

@Client.on_message(filters.command("p"))
async def get_crypto_price(client, message):
    if len(message.command) < 2:
        await message.reply("Kullanım: /p `coin`")
        return

    # Kullanıcının belirttiği kripto para sembolü
    coin_symbol = message.command[1].strip().upper() + "USDT"

    try:
        # Binance Futures API URL
        api_url = f"{BINANCE_FUTURES_API_URL}{coin_symbol}"

        # Asenkron GET isteği yaparak kripto para fiyatını al
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        price = data["lastPrice"]
                        high_price = data["highPrice"]
                        low_price = data["lowPrice"]
                        price_change = data["priceChangePercent"]
                        volume_usdt = float(data["quoteVolume"])

                        formatted_volume = format_large_number(volume_usdt)
                        
                        # Türkiye saatini al
                        tz = pytz.timezone('Europe/Istanbul')
                        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

                        response_message = (f"#{coin_symbol}\n"
                                            f"Fiyat: `${price}`\n"
                                            f"24h max: `${high_price}`\n"
                                            f"24h min: `${low_price}`\n"
                                            f"24h değişim: `%{price_change}`\n"
                                            f"Hacim: `${formatted_volume} USDT`\n\n"
                                            f"⏱:  `{current_time}`")
                        
                        await message.reply(response_message, parse_mode=enums.ParseMode.MARKDOWN)
                    else:
                        await message.reply("Belirtilen kripto para için fiyat bilgisi bulunamadı.")
                else:
                    await message.reply(f"Fiyat bilgisi alınırken bir hata oluştu. HTTP Durum Kodu: {response.status}")
    except Exception as e:
        await message.reply(f"Hata: {str(e)}. Lütfen daha sonra tekrar deneyin.")
