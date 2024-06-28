from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from heda import redis, log

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

@Client.on_message(filters.command(["start"]))
async def handle_start_command(_, message: Message):
    try:
        user_id = message.from_user.id
        start_message = (
            f"Merhaba! {message.from_user.mention}\n"
        )
        await message.reply_text(
            text=start_message,
            quote=True
        )
    
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name}."
        )

        new_user = await redis.is_added(
            "NEW_USER", user_id
        )
        if not new_user:
            await redis.add_to_db(
                "NEW_USER", user_id
            )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

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
