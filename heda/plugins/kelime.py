import requests
from pyrogram import Client, filters
import json

# Oyun durumu ve aktif grup için değişkenler
game_enabled = False
active_chat_id = None

# TDK kelime listesini çek ve dosyaya kaydet
def fetch_tdk_words():
    words = []
    base_url = "https://sozluk.gov.tr/gts_id?id="
    for i in range(1, 100000):  # TDK'da yaklaşık 92-93 bin kelime var
        response = requests.get(base_url + str(i))
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                word = data.get('madde')
                if word:
                    words.append(word)
        else:
            break
    return words

def save_words_to_file(words, filename="tdk_words.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        for word in words:
            file.write(word + "\n")

def load_words_from_file(filename="tdk_words.txt"):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

# Kelimeleri çek ve dosyaya kaydet
words = fetch_tdk_words()
save_words_to_file(words)
print(f"{len(words)} kelime kaydedildi.")

# Dosyadan kelimeleri yükle
kelime_listesi = load_words_from_file()

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
        if kelime in kelime_listesi:
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
