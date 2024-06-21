import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp
import json

# Kullanıcı alarmlarını saklamak için sözlük
user_alarms = {}

# Binance Futures API endpoint'i
BINANCE_FUTURES_API = "https://fapi.binance.com/fapi/v1/ticker/price"

async def check_price(symbol):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BINANCE_FUTURES_API}?symbol={symbol}USDT") as response:
            if response.status == 200:
                data = await response.json()
                return float(data['price'])
    return None

async def check_alarms():
    while True:
        for user_id, alarms in user_alarms.items():
            for alarm in alarms[:]:
                symbol, target_price = alarm
                current_price = await check_price(symbol)
                if current_price is not None:
                    if current_price >= target_price:
                        await app.send_message(user_id, f"🚨 Alarm: {symbol} fiyatı {current_price} USDT'ye ulaştı!")
                        alarms.remove(alarm)
        await asyncio.sleep(2)

@Client.on_message(filters.command("alarm") & filters.private)
async def handle_alarm(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()[1:]

    if len(args) == 0:
        await message.reply("Kullanım: /alarm <coin> <hedef_fiyat> veya /alarm sil veya /alarm liste")
        return

    if args[0].lower() == "sil":
        if user_id in user_alarms:
            del user_alarms[user_id]
            await message.reply("Tüm alarmlarınız silindi.")
        else:
            await message.reply("Aktif alarmınız bulunmamaktadır.")
        return

    if args[0].lower() == "liste":
        if user_id in user_alarms and user_alarms[user_id]:
            alarm_list = "\n".join([f"{coin}: {price} USDT" for coin, price in user_alarms[user_id]])
            await message.reply(f"Aktif alarmlarınız:\n{alarm_list}")
        else:
            await message.reply("Aktif alarmınız bulunmamaktadır.")
        return

    if len(args) != 2:
        await message.reply("Kullanım: /alarm <coin> <hedef_fiyat>")
        return

    coin, target_price = args[0].upper(), float(args[1])
    
    if user_id not in user_alarms:
        user_alarms[user_id] = []
    
    user_alarms[user_id].append((coin, target_price))
    await message.reply(f"Alarm kuruldu: {coin} için {target_price} USDT")

if __name__ == "__main__":
    app.start()
    asyncio.get_event_loop().create_task(check_alarms())
