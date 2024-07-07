from pyrogram import Client, filters
import rarfile
import os

# Tepki durumu için bir değişken
react_enabled = False

# /react komutunu dinleyin
@Client.on_message(filters.command("react"))
async def set_react_status(client, message):
    global react_enabled
    if len(message.command) > 1:
        if message.command[1].lower() == "on":
            react_enabled = True
            await message.reply("Tepkiler artık tüm kullanıcılar için etkin.")
        elif message.command[1].lower() == "off":
            react_enabled = False
            await message.reply("Tepkiler devre dışı bırakıldı.")
        else:
            await message.reply("Geçersiz komut. Kullanım: /react on veya /react off.")
    else:
        await message.reply("Geçersiz komut. Kullanım: /react on veya /react off.")

# Mesajları dinleyin ve tepki verin
@Client.on_message(filters.text)
async def react_to_message(client, message):
    global react_enabled
    if react_enabled and not message.text.startswith("/"):
        try:
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji="💘"
            )
        except Exception as e:
            await message.reply(f"Tepki gönderilemedi: {e}")

# /rar komutunu dinleyin
@Client.on_message(filters.command("rar"))
async def extract_rar_file(client, message):
    if len(message.command) > 1:
        rar_file_path = message.command[1]
        if os.path.exists(rar_file_path) and rar_file_path.endswith('.rar'):
            try:
                with rarfile.RarFile(rar_file_path) as rf:
                    file_list = rf.namelist()
                    if file_list:
                        await message.reply(f"RAR dosyası şu dosyaları içeriyor: {', '.join(file_list)}")
                        for file_name in file_list:
                            with rf.open(file_name) as file:
                                await client.send_document(
                                    chat_id=message.chat.id,
                                    document=file,
                                    file_name=file_name
                                )
                    else:
                        await message.reply("RAR dosyası boş.")
            except rarfile.Error as e:
                await message.reply(f"RAR dosyası açılamadı: {e}")
        else:
            await message.reply("Geçersiz dosya yolu veya RAR dosyası değil.")
    else:
        await message.reply("Lütfen RAR dosyasının yolunu belirtin. Kullanım: /rar <dosya_yolu>")
