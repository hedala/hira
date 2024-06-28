from pyrogram import Client, filters

# Tepki durumu için bir değişken
react_enabled = False

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
@Client.on_message(filters.text)
async def react_to_message(client, message):
    global react_enabled
    if react_enabled and not message.text.startswith("/"):
        try:
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji="❤️"
            )
        except Exception as e:
            await message.reply(f"Failed to send reaction: {e}")
            
