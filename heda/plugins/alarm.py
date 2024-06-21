import asyncio
import aiohttp
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from heda import redis, log

BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/ticker/price"

class AlarmSystem:
    def __init__(self, client: Client):
        self.client = client
        self.session = None
        self.running = False

    async def start(self):
        self.session = aiohttp.ClientSession()
        self.running = True
        asyncio.create_task(self.check_prices())

    async def stop(self):
        self.running = False
        if self.session:
            await self.session.close()

    async def check_prices(self):
        while self.running:
            try:
                log(__name__).info("API kontrol ediliyor...")
                all_alarms = await redis.db.keys("ALARM_*")
                for alarm_key in all_alarms:
                    user_id = alarm_key.split("_")[1]
                    user_alarms = json.loads(await redis.db.get(alarm_key) or "[]")
                    
                    for coin, target_price in user_alarms:
                        current_price = await self.get_price(f"{coin}USDT")
                        if current_price and current_price >= target_price:
                            await self.trigger_alarm(user_id, coin, current_price, target_price)
                            user_alarms.remove((coin, target_price))
                            if user_alarms:
                                await redis.db.set(alarm_key, json.dumps(user_alarms))
                            else:
                                await redis.db.delete(alarm_key)
            except Exception as e:
                log(__name__).error(f"Error in check_prices: {str(e)}")
            
            await asyncio.sleep(3)  # Her 3 saniyede bir kontrol et

    async def get_price(self, symbol: str) -> float:
        try:
            async with self.session.get(BINANCE_API_URL, params={"symbol": symbol}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["price"])
                else:
                    log(__name__).warning(f"Failed to fetch price for {symbol}. Status: {resp.status}")
        except Exception as e:
            log(__name__).error(f"Error fetching price for {symbol}: {str(e)}")
        return None

    async def trigger_alarm(self, user_id: int, coin: str, current_price: float, target_price: float):
        message = f"{coin} hedef fiyata ulaştı! Hedef: {target_price}, Şu anki fiyat: {current_price}"
        await self.client.send_message(int(user_id), message)
        log(__name__).info(f"Alarm triggered for user {user_id}: {message}")

alarm_system = None

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
                alarms_list = json.loads(alarms)
                alarm_text = "\n".join([f"{coin}: {price}" for coin, price in alarms_list])
                await message.reply_text(f"Aktif alarmlarınız:\n{alarm_text}")
            return

        if len(command) != 3:
            await message.reply_text("Lütfen bir coin ve fiyat belirtin.")
            return

        coin = command[1].upper()
        try:
            price = float(command[2])
        except ValueError:
            await message.reply_text("Geçersiz fiyat. Lütfen sayısal bir değer girin.")
            return

        current_alarms = json.loads(await redis.db.get(f"ALARM_{user_id}") or "[]")
        current_alarms.append((coin, price))
        await redis.db.set(f"ALARM_{user_id}", json.dumps(current_alarms))

        await message.reply_text(f"{coin} için {price} fiyat alarmı kuruldu.")

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text("Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

async def start_alarm_system(client: Client):
    global alarm_system
    alarm_system = AlarmSystem(client)
    await alarm_system.start()
