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

# Cache dictionary to store the results and timestamps
cache = {
    "top_gainers": {},
    "top_losers": {},
    "timestamp": None
}

# User state to track primary button selection
user_state = {}

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

async def update_cache(interval, top=True):
    try:
        changes = await get_movers(interval)
        category = "top_gainers" if top else "top_losers"
        cache[category][interval] = format_response(changes, interval, top=top)
        cache["timestamp"] = datetime.utcnow()
    except Exception as e:
        log.error(f"Cache update error: {str(e)}")

async def periodic_cache_update():
    while True:
        await update_cache("15m", top=True)
        await update_cache("15m", top=False)
        await asyncio.sleep(20)
        await update_cache("1h", top=True)
        await update_cache("1h", top=False)
        await asyncio.sleep(40)
        await update_cache("4h", top=True)
        await update_cache("4h", top=False)
        await asyncio.sleep(60)
        await update_cache("1d", top=True)
        await update_cache("1d", top=False)
        await asyncio.sleep(80)

@Client.on_message(filters.command("ch"))
async def send_initial_buttons(client, message):
    now = datetime.utcnow()
    if cache["timestamp"] and (now - cache["timestamp"]) < timedelta(minutes=1):
        cache_is_fresh = True
    else:
        cache_is_fresh = False

    if not cache_is_fresh:
        await update_cache("1h", top=True)
        await update_cache("1h", top=False)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yükselenler", callback_data="top_gainers"), InlineKeyboardButton("Düşenler", callback_data="top_losers")],
        [InlineKeyboardButton("15M", callback_data="15m"), InlineKeyboardButton("1H", callback_data="1h"), InlineKeyboardButton("4H", callback_data="4h"), InlineKeyboardButton("1D", callback_data="1d")]
    ])
    user_state[message.from_user.id] = {"top": True, "period": "1h"}
    await message.reply("Lütfen bir seçenek seçin:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"\b(top_losers|top_gainers|15m|1h|4h|1d)\b"))
async def handle_callback_query(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data in ["top_gainers", "top_losers"]:
        user_state[user_id]["top"] = (data == "top_gainers")
    elif data in ["15m", "1h", "4h", "1d"]:
        user_state[user_id]["period"] = data

    top = user_state[user_id]["top"]
    period = user_state[user_id]["period"]

    response_message = cache["top_gainers" if top else "top_losers"].get(period, "Veri bulunamadı.")
    await callback_query.answer("Veriler getiriliyor, lütfen bekleyin...")
    
    if callback_query.message.text != response_message:
        await callback_query.message.edit_text(response_message, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=callback_query.message.reply_markup)

# Start the cache update task
loop = asyncio.get_event_loop()
loop.create_task(periodic_cache_update())
