import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp
import json

# Kullanıcı alarmlarını saklamak için sözlük
user_alarms = {}

async def check_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}USDT"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
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

@Client.on_message(filters.command("st"))
async def start_command(client, message: Message):
    await message.reply_text("Merhaba! Kripto alarm botuna hoş geldiniz. Alarm kurmak için /alarm komutunu kullanabilirsiniz.")

@Client.on_message(filters.command("aalarm"))
async def alarm_command(client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) == 1:
        await message.reply_text("Kullanım: /alarm <coin> <hedef_fiyat> veya /alarm sil veya /alarm liste")
        return

    if command_parts[1].lower() == "sil":
        if user_id in user_alarms:
            del user_alarms[user_id]
            await message.reply_text("Tüm alarmlarınız silindi.")
        else:
            await message.reply_text("Aktif alarmınız bulunmamaktadır.")
        return

    if command_parts[1].lower() == "liste":
        if user_id in user_alarms and user_alarms[user_id]:
            alarm_list = "\n".join([f"{symbol}: {price} USDT" for symbol, price in user_alarms[user_id]])
            await message.reply_text(f"Aktif alarmlarınız:\n{alarm_list}")
        else:
            await message.reply_text("Aktif alarmınız bulunmamaktadır.")
        return

    if len(command_parts) != 3:
        await message.reply_text("Kullanım: /alarm <coin> <hedef_fiyat>")
        return

    symbol = command_parts[1].upper()
    try:
        target_price = float(command_parts[2])
    except ValueError:
        await message.reply_text("Geçersiz hedef fiyat. Lütfen sayısal bir değer girin.")
        return

    if user_id not in user_alarms:
        user_alarms[user_id] = []
    user_alarms[user_id].append((symbol, target_price))
    await message.reply_text(f"Alarm kuruldu: {symbol} için {target_price} USDT")

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(check_alarms())
