from pyrogram import Client, filters
import random

# Tepki durumu için bir değişken
react_enabled = False

# Kullanılacak kalp emojileri
heart_emojis = ["💘", "❤️", "💓", "💔", "💖", "💗", "💙", "💚", "💛", "🧡", "💜", "🤎", "🖤"]

# /react komutunu dinleyin
@Client.on_message(filters.command("react"))
async def set_react_status(client, message):
    global react_enabled
    if len(message.command) > 1:
        if message.command[1].lower() == "on":
            react_enabled = True
            await message.reply("Reactions are now enabled for all users.")
        elif message.command[1].lower() == "off":
            react_enabled = False
            await message.reply("Reactions are now disabled.")
        else:
            await message.reply("Invalid command. Use /react on or /react off.")
    else:
        await message.reply("Invalid command. Use /react on or /react off.")

# Mesajları dinleyin ve tepki verin
@Client.on_message(filters.group)
async def react_to_message(client, message):
    global react_enabled
    if react_enabled and not message.text.startswith("/"):
        try:
            random_emoji = random.choice(heart_emojis)
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=random_emoji
            )
        except Exception as e:
            await message.reply(f"Failed to send reaction: {e}")
