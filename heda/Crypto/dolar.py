from pyrogram import Client, filters
from pyrogram.types import Message
import requests

from heda import redis, log

# Binance API'si için URL
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=USDTTRY"

def get_exchange_rate():
    try:
        response = requests.get(BINANCE_API_URL)
        data = response.json()
        if "price" in data:
            usd_to_try = float(data["price"])
            return usd_to_try
        else:
            log(__name__).error("Error fetching exchange rate data.")
            return None
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        return None

@Client.on_message(filters.command(["dolar"]))
async def handle_dolar_command(client: Client, message: Message):
    try:
        exchange_rate = get_exchange_rate()
        if exchange_rate is None:
            await message.reply_text("Döviz kuru bilgisi alınamadı.")
            return

        command_parts = message.text.split()
        if len(command_parts) == 1:
            await message.reply_text(f"1 Dolar = {exchange_rate:.2f} TL")
        elif len(command_parts) == 2:
            amount = float(command_parts[1])
            converted_amount = amount * exchange_rate
            await message.reply_text(f"{amount} Dolar = {converted_amount:.2f} TL")
        else:
            await message.reply_text("Geçersiz komut kullanımı. Doğru kullanım: `/dolar` veya `/dolar <sayı>`")
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

@Client.on_message(filters.command(["tl"]))
async def handle_tl_command(client: Client, message: Message):
    try:
        exchange_rate = get_exchange_rate()
        if exchange_rate is None:
            await message.reply_text("Döviz kuru bilgisi alınamadı.")
            return

        command_parts = message.text.split()
        if len(command_parts) == 2:
            amount = float(command_parts[1])
            converted_amount = amount / exchange_rate
            await message.reply_text(f"{amount} TL = {converted_amount:.2f} Dolar")
        else:
            await message.reply_text("Geçersiz komut kullanımı. Doğru kullanım: `/tl <sayı>`")
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
