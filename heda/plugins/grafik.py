from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import asyncio
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np
import os

# Logger ayarları
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Binance Futures API URLs
BINANCE_FUTURES_TICKER_API_URL = "https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
BINANCE_FUTURES_KLINES_API_URL = "https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"

# Chart settings
TIMEFRAMES = {"15m": "15 minute", "1h": "1 hour", "4h": "4 hour", "1d": "1 day"}

# RSI calculation
def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period), 'valid') / period
    avg_loss = np.convolve(loss, np.ones(period), 'valid') / period
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi[-1] if len(rsi) > 0 else None

async def fetch_latest_price(session, symbol):
    url = BINANCE_FUTURES_TICKER_API_URL.format(symbol=symbol)
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return float(data['price'])
        else:
            raise Exception(f"Failed to fetch latest price for {symbol}: HTTP {response.status}")

async def fetch_kline(session, symbol, interval, limit=100):
    url = BINANCE_FUTURES_KLINES_API_URL.format(symbol=symbol, interval=interval, limit=limit)
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Failed to fetch klines for {symbol}: HTTP {response.status}")

def calculate_change(open_price, current_price):
    return ((current_price - open_price) / open_price) * 100

async def generate_chart(symbol, interval):
    async with aiohttp.ClientSession() as session:
        kline_data = await fetch_kline(session, symbol, interval, limit=100)
    
    df = pd.DataFrame(kline_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', '_', '_', '_', '_', '_', '_'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    
    rsi = calculate_rsi(df['close'].values)
    
    # Fetch the latest price to draw the line
    latest_price = df['close'].iloc[-1]

    # Customize chart style
    mc = mpf.make_marketcolors(up='g', down='r', edge='inherit', wick='inherit', volume='inherit')
    s = mpf.make_mpf_style(marketcolors=mc, figcolor='#040720', gridcolor='#d9d9d9', facecolor='#040720')
    
    fig, ax = mpf.plot(df, type='candle', style=s, returnfig=True, title=f'{symbol} - {TIMEFRAMES[interval]}', ylabel='Price', volume=True, figsize=(16, 9))
    
    # Display RSI
    ax[0].text(0.5, 0.02, f'RSI: {rsi:.2f}', horizontalalignment='center', verticalalignment='center', transform=ax[0].transAxes, fontsize=12, color='white', bbox=dict(facecolor='#040720', alpha=0.8))
    
    # Draw a line for the latest price
    ax[0].axhline(latest_price, color='white', linestyle='--')
    ax[0].text(df.index[-1], latest_price, f'{latest_price:.2f}', color='white', verticalalignment='bottom')

    # Create charts directory if it doesn't exist
    os.makedirs('charts', exist_ok=True)
    
    chart_path = f'charts/{symbol}_{interval}.png'
    fig.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return chart_path

@Client.on_message(filters.command("grafik"))
async def send_chart(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Lütfen bir coin sembolü belirtin (örn: /grafik BTC).")
        return
    
    symbol = args[1].upper() + "USDT"
    interval = "15m"  # Default interval
    
    chart_path = await generate_chart(symbol, interval)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("15M", callback_data=f"{symbol}_15m"), InlineKeyboardButton("1H", callback_data=f"{symbol}_1h"), InlineKeyboardButton("4H", callback_data=f"{symbol}_4h"), InlineKeyboardButton("1D", callback_data=f"{symbol}_1d")]
    ])
    
    await message.reply_photo(chart_path, caption=f"{symbol} - {TIMEFRAMES[interval]}", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"\b([A-Z]+USDT)_(15m|1h|4h|1d)\b"))
async def handle_chart_callback(client, callback_query):
    data = callback_query.data
    symbol, interval = data.split('_')
    
    chart_path = await generate_chart(symbol, interval)
    
    await callback_query.message.edit()  # Remove the old message with the chart
    await callback_query.message.reply_photo(chart_path, caption=f"{symbol} - {TIMEFRAMES[interval]}", reply_markup=callback_query.message.reply_markup)
