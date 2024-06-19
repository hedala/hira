from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import asyncio
import matplotlib.pyplot as plt
import io
from datetime import datetime

# Binance Futures API URLs
BINANCE_FUTURES_KLINES_API_URL = "https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"

async def fetch_klines(symbol, interval, limit=60):
    url = BINANCE_FUTURES_KLINES_API_URL.format(symbol=symbol, interval=interval, limit=limit)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch klines for {symbol}: HTTP {response.status}")

def plot_chart(klines, symbol):
    timestamps = [datetime.fromtimestamp(int(k[0]) / 1000) for k in klines]
    prices = [float(k[4]) for k in klines]  # Closing prices

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, prices, label=f'{symbol} Price')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title(f'{symbol} 1H Price Chart')
    plt.legend()
    plt.grid(True)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer

@Client.on_message(filters.command("grafik"))
async def send_price_chart(client, message):
    try:
        symbol = message.text.split()[1].upper() + 'USDT'
        interval = '1h'
        
        klines = await fetch_klines(symbol, interval, limit=60)
        chart_buffer = plot_chart(klines, symbol)
        
        await message.reply_photo(chart_buffer, caption=f"{symbol} 1H Price Chart")
    except IndexError:
        await message.reply("Lütfen bir coin sembolü belirtin. Örnek: /grafik BTC")
    except Exception as e:
        await message.reply(f"Hata: {str(e)}")
