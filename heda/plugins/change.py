from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import asyncio
from datetime import datetime, timedelta
import pytz
import logging

# Logger ayarları
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Binance Futures API URLs
BINANCE_FUTURES_EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
BINANCE_FUTURES_TICKER_API_URL = "https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
BINANCE_FUTURES_KLINES_API_URL = "https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=1"

# Cache dictionary to store the results and timestamp
cache = {
    "top_gainers": {},
    "top_losers": {},
    "timestamp": None
}

user_choices = {}

def format_large_number(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    else:
        return f"{num:.2f}"

async def fetch_all_symbols():
    async with aiohttp.ClientSession() as session:
        async with session.get(BINANCE_FUTURES_EXCHANGE_INFO_URL) as response:
            if response.status == 200:
                data = await response.json()
                symbols = [item['symbol'] for item in data['symbols'] if item['symbol'].endswith('USDT')]
                return symbols
            else:
                raise Exception(f"Failed to fetch symbols: HTTP {response.status}")

async def fetch_latest_price(session, symbol):
    url = BINANCE_FUTURES_TICKER_API_URL.format(symbol=symbol)
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return float(data['price'])
        else:
            raise Exception(f"Failed to fetch latest price for {symbol}: HTTP {response.status}")

async def fetch_kline(session, symbol, interval):
    url = BINANCE_FUTURES_KLINES_API_URL.format(symbol=symbol, interval=interval)
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Failed to fetch klines for {symbol}: HTTP {response.status}")

def calculate_change(open_price, current_price):
    return ((current_price - open_price) / open_price) * 100

async def get_movers(interval):
    symbols = await fetch_all_symbols()
    changes = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            tasks.append(asyncio.create_task(fetch_kline(session, symbol, interval)))
            tasks.append(asyncio.create_task(fetch_latest_price(session, symbol)))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i in range(0, len(responses), 2):
            kline_data, current_price = responses[i], responses[i+1]
            if isinstance(kline_data, Exception) or isinstance(current_price, Exception):
                continue
            open_price = float(kline_data[0][1])  # Open price of the current interval
            change = calculate_change(open_price, current_price)
            changes.append((symbols[i//2], change))
    
    return changes

def format_response(changes, period, top=True):
    sorted_changes = sorted(changes, key=lambda x: x[1], reverse=top)[:6]
    response_message = f"**{period} İçerisinde En Çok {'Yükselen' if top else 'Düşen'} 6 Coin**\n"
    for symbol, change in sorted_changes:
        response_message += f"{symbol}: %{change:.2f}\n"
    return response_message

async def update_cache():
    while True:
        try:
            # İlk olarak yükselenleri al
            for interval in ["15m", "1h", "4h", "1d"]:
                changes = await get_movers(interval)
                cache["top_gainers"][interval] = format_response(changes, interval, top=True)
            await asyncio.sleep(20)  # 20 saniye bekle

            # Ardından düşenleri al
            for interval in ["15m", "1h", "4h", "1d"]:
                changes = await get_movers(interval)
                cache["top_losers"][interval] = format_response(changes, interval, top=False)
            cache["timestamp"] = datetime.utcnow()  # Update cache timestamp
            await asyncio.sleep(60)  # 1 dakika bekle
        except Exception as e:
            log.error(f"Cache update error: {str(e)}")

@Client.on_message(filters.command("ch"))
async def send_initial_buttons(client, message):
    now = datetime.utcnow()
    if cache["timestamp"] and (now - cache["timestamp"]).total_seconds() < 60:
        log.info("Using cached data")
    else:
        log.info("Refreshing cache data")
        await update_cache()
        
    user_choices[message.chat.id] = {"main": None, "interval": None}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yükselenler", callback_data="top_gainers"), InlineKeyboardButton("Düşenler", callback_data="top_losers")],
        [InlineKeyboardButton("15M", callback_data="15m"), InlineKeyboardButton("1H", callback_data="1h"), InlineKeyboardButton("4H", callback_data="4h"), InlineKeyboardButton("1D", callback_data="1d")]
    ])
    await message.reply("Lütfen bir seçenek seçin:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"\b(top_losers|top_gainers|15m|1h|4h|1d)\b"))
async def handle_callback_query(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    if data in ["top_gainers", "top_losers"]:
        user_choices[chat_id]["main"] = data
        await callback_query.answer(f"{data} seçildi. Zaman aralığı seçin.")
    elif data in ["15m", "1h", "4h", "1d"]:
        user_choices[chat_id]["interval"] = data
        main_choice = user_choices[chat_id]["main"]
        
        if not main_choice:
            await callback_query.answer("Lütfen önce ana bir seçim yapın.", show_alert=True)
            return
        
        await callback_query.answer("Veriler getiriliyor, lütfen bekleyin...")
        
        try:
            response_message = cache[main_choice].get(data, "Veri bulunamadı.")
            if callback_query.message.text != response_message:
                await callback_query.message.edit_text(response_message, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=callback_query.message.reply_markup)
        except Exception as e:
            log.error(f"Callback query error: {str(e)}")
            await callback_query.answer("Bir hata oluştu, lütfen daha sonra tekrar deneyin.")

# Start the cache update task
loop = asyncio.get_event_loop()
loop.create_task(update_cache())
