import requests
from pyrogram import Client, filters
import json

# Oyun durumu ve aktif grup için değişkenler
game_enabled = False
active_chat_id = None

# TDK API'sini kullanarak kelimenin var olup olmadığını kontrol et
def check_word_in_tdk(word):
    base_url = "https://sozluk.gov.tr/gts?ara="
    try:
        response = requests.get(base_url + word)
        response.raise_for_status()
        data = response.json()
        if data and 'error' not in data:
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error checking word {word}: {e}")
    return False

# /kelime komutunu dinleyin
@Client.on_message(filters.command("kelime"))
async def set_game_status(client, message):
    global game_enabled, active_chat_id
    if len(message.command) > 1:
        command = message.command[1].lower()
        if command == "on":
            game_enabled = True
            active_chat_id = message.chat.id
            await message.reply("Kelime oyunu bu grupta aktif edildi.")
        elif command == "off":
            game_enabled = False
            active_chat_id = None
            await message.reply("Kelime oyunu devre dışı bırakıldı.")
        else:
            await message.reply("Geçersiz komut. Kullanım: /kelime on veya /kelime off.")
    else:
        await message.reply("Geçersiz komut. Kullanım: /kelime on veya /kelime off.")

# Mesajları dinleyin ve kelime kontrolü yapın
@Client.on_message(filters.text)
async def word_game(client, message):
    global game_enabled, active_chat_id
    if game_enabled and message.chat.id == active_chat_id and not message.text.startswith("/"):
        kelime = message.text.strip().lower()
        if check_word_in_tdk(kelime):
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji="❤️"
            )
        else:
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji="💔"
            )
