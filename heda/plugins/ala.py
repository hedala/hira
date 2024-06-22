from pyrogram import Client, filters, enums
import aiohttp
import asyncio
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from InflexMusic import app

# Binance Futures API URL
BINANCE_FUTURES_API_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol="

# Data structure for alarms
alarms = {}

def format_large_number(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    else:
        return f"{num:.2f}"

@app.on_message(filters.command("f"))
async def get_crypto_price(client, message):
    if len(message.command) < 2:
        await message.reply("Kullanım: /f <coin>")
        return

    coin_symbol = message.command[1].strip().upper() + "USDT"

    try:
        api_url = f"{BINANCE_FUTURES_API_URL}{coin_symbol}"

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

@Client.on_message(filters.command("alarm"))
async def set_alarm(client, message):
    if len(message.command) < 3:
        await message.reply("Kullanım: /alarm <coin> <fiyat>")
        return

    coin_symbol = message.command[1].strip().upper() + "USDT"
    target_price = float(message.command[2].strip())

    chat_id = message.chat.id

    if chat_id not in alarms:
        alarms[chat_id] = []

    alarms[chat_id].append({
        "coin_symbol": coin_symbol,
        "target_price": target_price,
    })

    await message.reply(f"Alarm kuruldu: {coin_symbol} fiyatı {target_price}'e ulaşınca bilgilendirileceksiniz.")

@Client.on_message(filters.command("alarm_sil"))
async def delete_alarms(client, message):
    chat_id = message.chat.id

    if chat_id in alarms:
        del alarms[chat_id]
        await message.reply("Tüm alarmlar silindi.")
    else:
        await message.reply("Hiç alarm kurmamışsınız.")

@Client.on_message(filters.command("alarm_list"))
async def list_alarms(client, message):
    chat_id = message.chat.id

    if chat_id in alarms and alarms[chat_id]:
        alarm_list = "\n".join([f"{alarm['coin_symbol']} - {alarm['target_price']}" for alarm in alarms[chat_id]])
        await message.reply(f"Kurulu Alarmlar:\n{alarm_list}")
    else:
        await message.reply("Hiç alarm kurmamışsınız.")

async def check_alarms():
    if alarms:
        for chat_id, alarm_list in alarms.items():
            for alarm in alarm_list:
                coin_symbol = alarm["coin_symbol"]
                target_price = alarm["target_price"]

                try:
                    api_url = f"{BINANCE_FUTURES_API_URL}{coin_symbol}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(api_url) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data:
                                    current_price = float(data["lastPrice"])

                                    if current_price >= target_price:
                                        await app.send_message(chat_id, f"Alarm! {coin_symbol} fiyatı {target_price}'e ulaştı. Şu anki fiyat: {current_price}")
                                        alarm_list.remove(alarm)

                except Exception as e:
                    print(f"Hata: {str(e)}")

# APScheduler setup
scheduler = AsyncIOScheduler()
scheduler.add_job(check_alarms, "interval", seconds=2)
scheduler.start()
