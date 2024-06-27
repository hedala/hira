from pyrogram import Client, filters
from pyrogram.raw.functions.messages import SendReaction
from pyrogram.raw.types import ReactionEmoji

# Tepki durumu için bir değişken
react_enabled = True

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
@Client.on_message(filters.text & ~filters.command)
async def react_to_message(client, message):
    global react_enabled
    if react_enabled:
        for bot in bots:
            await bot.invoke(SendReaction(
                peer=await bot.resolve_peer(message.chat.id),
                msg_id=message.message_id,
                reaction=[ReactionEmoji(emoticon='❤️')]
            ))
