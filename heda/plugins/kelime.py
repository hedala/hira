from pyrogram import Client, filters
import json

# Oyun durumu ve aktif grup için değişkenler
game_enabled = False
active_chat_id = None

# TDK kelime listesini yükleyin
kelime_listesi = [
    "elma", "armut", "muz", "çilek", "kiraz", "karpuz", "kavun", "portakal", "mandalina", "üzüm",
    "vişne", "şeftali", "kayısı", "erik", "nar", "avokado", "ananas", "kivi", "hindistancevizi", "greyfurt",
    "limon", "incir", "dut", "ahududu", "böğürtlen", "yabanmersini", "frambuaz", "karadut", "çilek", "kızılcık",
    "kavun", "karpuz", "üzüm", "elma", "armut", "muz", "çilek", "kiraz", "portakal", "mandalina",
    "vişne", "şeftali", "kayısı", "erik", "nar", "avokado", "ananas", "kivi", "hindistancevizi", "greyfurt",
    "limon", "incir", "dut", "ahududu", "böğürtlen", "yabanmersini", "frambuaz", "karadut", "çilek", "kızılcık",
    "kavun", "karpuz", "üzüm", "elma", "armut", "muz", "çilek", "kiraz", "portakal", "mandalina",
    "vişne", "şeftali", "kayısı", "erik", "nar", "avokado", "ananas", "kivi", "hindistancevizi", "greyfurt",
    "limon", "incir", "dut", "ahududu", "böğürtlen", "yabanmersini", "frambuaz", "karadut", "çilek", "kızılcık",
    "kavun", "karpuz", "üzüm", "elma", "armut", "muz", "çilek", "kiraz", "portakal", "mandalina"
]

# /kelime komutunu dinleyin
@Client.on_message(filters.command("kelime"))
async def set_game_status(client, message):
    global game_enabled, active_chat_id
    if len(message.command) > 1:
        if message.command[1].lower() == "on":
            game_enabled = True
            active_chat_id = message.chat.id
            await message.reply("Kelime oyunu bu grupta aktif edildi.")
        elif message.command[1].lower() == "off":
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
                emoji="✅"
            )
        else:
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji="❌"
            )
