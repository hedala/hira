from pyrogram import Client, filters

# Kullanıcı dil tercihi
user_lang = {}

@Client.on_message(filters.command("start"))
async def start_hello(client, message):
    if user_lang.get(message.from_user.id) == "en":
        await message.reply("hello")
    elif user_lang.get(message.from_user.id) == "tr":
        await message.reply("merhaba")
    else:
        await message.reply("Please set your language using /lang en or /lang tr.")

@Client.on_message(filters.command(["lang"]))
async def set_language(client, message):
    lang = message.text.split()[1]
    if lang in ["en", "tr"]:
        user_lang[message.from_user.id] = lang
        await message.reply(f"Language set to {'English' if lang == 'en' else 'Turkish'}.")
    else:
        await message.reply("Invalid language code. Use /lang en or /lang tr.")

if __name__ == "__main__":
