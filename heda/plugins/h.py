from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Kullanıcı dil tercihi
user_lang = {}

languages = {
    "en": "🇺🇸 English",
    "tr": "🇹🇷 Türkçe",
    "ja": "🇯🇵 日本語 (Japanese)",
    "ko": "🇰🇷 한국어 (Korean)",
    "zh": "🇨🇳 中文 (Chinese)",
    "fr": "🇫🇷 Français (French)",
    "es": "🇪🇸 Español (Spanish)"
}

# Mesajlar
messages = {
    "start": {
        "en": "Hello, {mention}",
        "tr": "Merhaba, {mention}",
        "ja": "こんにちは, {mention}",
        "ko": "안녕하세요, {mention}",
        "zh": "你好, {mention}",
        "fr": "Bonjour, {mention}",
        "es": "Hola, {mention}"
    },
    "lang_set": {
        "en": "Language set to English.",
        "tr": "Dil Türkçe olarak ayarlandı.",
        "ja": "言語が日本語に設定されました。",
        "ko": "언어가 한국어로 설정되었습니다.",
        "zh": "语言设置为中文。",
        "fr": "Langue définie sur le français.",
        "es": "Idioma configurado a español."
    },
    "invalid_lang": {
        "en": "Invalid language code. Use /lang to choose a language.",
        "tr": "Geçersiz dil kodu. Dil seçmek için /lang kullanın.",
        "ja": "無効な言語コードです。言語を選択するには /lang を使用してください。",
        "ko": "잘못된 언어 코드입니다. 언어를 선택하려면 /lang 을 사용하십시오.",
        "zh": "无效的语言代码。使用 /lang 选择语言。",
        "fr": "Code de langue invalide. Utilisez /lang pour choisir une langue.",
        "es": "Código de idioma inválido. Use /lang para elegir un idioma."
    }
}

@Client.on_message(filters.command("start"))
async def start_hello(client, message):
    lang = user_lang.get(message.from_user.id, "en")
    mention = message.from_user.mention
    await message.reply(messages["start"][lang].format(mention=mention))

@Client.on_message(filters.command("lang"))
async def set_language(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(languages[code], callback_data=code) for code in ["en", "tr"]],
        [InlineKeyboardButton(languages[code], callback_data=code) for code in ["ja", "ko"]],
        [InlineKeyboardButton(languages[code], callback_data=code) for code in ["zh", "fr"]],
        [InlineKeyboardButton(languages[code], callback_data=code) for code in ["es"]]
    ])
    await message.reply("Choose your language:", reply_markup=keyboard)

@Client.on_callback_query()
async def callback_query_handler(client, callback_query):
    lang = callback_query.data
    user_lang[callback_query.from_user.id] = lang
    await callback_query.answer()
    await callback_query.message.edit_text(messages["lang_set"][lang])
