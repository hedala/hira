from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Ana help mesajı
help_message = "Lütfen görmek istediğiniz komut kategorisini seçin:"

# Kripto komutları
crypto_commands = """
Kripto Komutları:
/price <coin> - Belirtilen kripto para biriminin fiyatını gösterir
/market - Genel piyasa durumunu gösterir
/portfolio - Kripto portföyünüzü görüntüler
"""

# Genel komutlar
general_commands = """
Genel Komutlar:
/start - Botu başlatır
/help - Bu yardım mesajını gösterir
/info - Bot hakkında bilgi verir
/settings - Bot ayarlarını değiştirir
"""

# Help komutu için işleyici
@Client.on_message(filters.command("help"))
async def help_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Kripto Komutları", callback_data="crypto_help")],
        [InlineKeyboardButton("Genel Komutlar", callback_data="general_help")]
    ])
    
    await message.reply_text(help_message, reply_markup=keyboard)

# Callback query işleyicisi
@Client.on_callback_query()
async def callback_query_handler(client, query):
    if query.data == "crypto_help":
        await query.answer()
        await query.message.edit_text(crypto_commands, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Geri", callback_data="back_to_main")]
        ]))
    elif query.data == "general_help":
        await query.answer()
        await query.message.edit_text(general_commands, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Geri", callback_data="back_to_main")]
        ]))
    elif query.data == "back_to_main":
        await query.answer()
        await query.message.edit_text(help_message, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Kripto Komutları", callback_data="crypto_help")],
            [InlineKeyboardButton("Genel Komutlar", callback_data="general_help")]
        ]))
