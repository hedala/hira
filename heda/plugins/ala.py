import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# In-memory storage for alarms
alarms = {}

async def get_coin_price(coin):
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={coin.upper()}USDT'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return float(data['price'])

async def price_check():
    while True:
        for user_id, user_alarms in alarms.items():
            for coin, target_price in user_alarms.copy().items():
                current_price = await get_coin_price(coin)
                if current_price >= target_price:
                    await client.send_message(user_id, f"🚨 {coin.upper()} has reached the target price of {target_price} USDT! Current price: {current_price} USDT")
                    del alarms[user_id][coin]
        await asyncio.sleep(2)

@Client.on_message(filters.command(["alarm"]))
async def set_alarm(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /alarm <coin> <target_price>")
        return

    coin = args[1].upper()
    try:
        target_price = float(args[2])
    except ValueError:
        await message.reply("Invalid target price. Please enter a valid number.")
        return

    user_id = message.from_user.id
    if user_id not in alarms:
        alarms[user_id] = {}

    alarms[user_id][coin] = target_price
    await message.reply(f"Alarm set for {coin} at {target_price} USDT")

@Client.on_message(filters.command(["alarm_delete"]))
async def delete_alarms(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in alarms:
        del alarms[user_id]
        await message.reply("All your alarms have been deleted.")
    else:
        await message.reply("You have no alarms to delete.")

@Client.on_message(filters.command(["alarm_list"]))
async def list_alarms(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in alarms and alarms[user_id]:
        response = "Your active alarms:\n"
        for coin, target_price in alarms[user_id].items():
            response += f"- {coin} at {target_price} USDT\n"
        await message.reply(response)
    else:
        await message.reply("You have no active alarms.")

async def main():
    async with client:
        # Başlangıçta fiyat kontrolünü başlatır
        asyncio.create_task(price_check())
        await client.idle()
