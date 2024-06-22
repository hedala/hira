import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from heda import redis, log

# Binance Futures API endpoint
BINANCE_FUTURES_API = "https://fapi.binance.com/fapi/v1/ticker/price?symbol="

# Fonksiyon: Binance Futures API'den coin fiyatını almak için
async def get_coin_price(coin: str) -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BINANCE_FUTURES_API}{coin}USDT") as response:
            data = await response.json()
            return float(data["price"])

# Komut: /b <coin>
@Client.on_message(filters.command(["b"]))
async def handle_b_command(client: Client, message: Message):
    try:
        # Coin ismini al
        coin = message.text.split()[1].upper()
        
        # Coin fiyatını al
        price = await get_coin_price(coin)

        # Mesajı butonla birlikte gönder
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"🔄 Fiyatı güncelle", callback_data=f"update_price:{coin}")]
            ]
        )
        await message.reply_text(
            f"{coin} fiyatı: {price} USDT",
            reply_markup=keyboard
        )

    except Exception as e:
        log(__name__).error(f"Error in handle_b_command: {str(e)}")
        await message.reply_text("Bir hata oluştu. Lütfen komutu doğru formatta kullanın: /b <coin>")

# Callback: Fiyat güncellemesi
@Client.on_callback_query(filters.regex(r"update_price:(.+)"))
async def handle_update_price(client: Client, callback_query: CallbackQuery):
    try:
        # Coin ismini al
        coin = callback_query.data.split(":")[1]

        # Coin fiyatını al
        price = await get_coin_price(coin)

        # Fiyatı güncellenmiş olarak gönder
        await callback_query.message.edit_text(
            f"{coin} fiyatı: {price} USDT",
            reply_markup=callback_query.message.reply_markup
        )

    except Exception as e:
        log(__name__).error(f"Error in handle_update_price: {str(e)}")
        await callback_query.answer("Çok fazla istek. Lütfen az sonra tekrar deneyiniz.")
