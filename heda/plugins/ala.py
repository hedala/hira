import asyncio
import aiohttp
import json
from pyrogram import Client, filters
from pyrogram.types import Message

from heda import redis, log

BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/ticker/price"

@Client.on_message(filters.command(["aalarm"]))
async def handle_alarm_command(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        command = message.command

        if len(command) == 1:
            await message.reply_text("Lütfen bir coin ve fiyat belirtin.")
            return

        if command[1] == "sil":
            await redis.db.delete(f"ALARM_{user_id}")
            await message.reply_text("Tüm alarmlarınız silindi.")
            return

        if command[1] == "list":
            alarms = await redis.db.get(f"ALARM_{user_id}")
            if not alarms:
                await message.reply_text("Aktif bir alarmınız yok.")
            else:
                await message.reply_text(f"Aktif alarmlarınız: {alarms}")
            return

        if len(command) != 3:
            await message.reply_text("Lütfen bir coin ve fiyat belirtin.")
            return

        coin = command[1]
        price = float(command[2])

        current_alarms = json.loads(await redis.db.get(f"ALARM_{user_id}") or "[]")
        current_alarms.append((coin, price))
        await redis.db.set(f"ALARM_{user_id}", json.dumps(current_alarms))

        await message.reply_text(f"{coin} için {price} fiyat alarmı kuruldu.")

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

async def check_price():
    async with aiohttp.ClientSession() as session:
        while True:
            alarms = json.loads(await redis.db.get("ALARM") or "{}")
            for user_id, user_alarms in alarms.items():
                user_alarms = json.loads(user_alarms)
                for coin, target_price in user_alarms:
                    async with session.get(BINANCE_API_URL, params={"symbol": coin}) as resp:
                        data = await resp.json()
                        if float(data["price"]) >= target_price:
                            await client.send_message(user_id, f"{coin} hedef fiyata ulaştı!")
                            user_alarms.remove((coin, target_price))
                            await redis.db.set(f"ALARM_{user_id}", json.dumps(user_alarms))
            await asyncio.sleep(1)

asyncio.create_task(check_price())
