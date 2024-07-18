import os
import base64
import requests
from user_agent import generate_user_agent
from pyrogram import Client, filters

def get_ss(link, name="screenshot.png"):
    headers = {
        "authority": "api.apilight.com",
        "accept": "text/plain, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7",
        "origin": "https://urltoscreenshot.com",
        "referer": "https://urltoscreenshot.com/",
        "sec-ch-ua": "'Not-A.Brand';v='99', 'Chromium';v='124'",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "'Android'",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": generate_user_agent(),
        "x-api-key": "j1gIaMwfU545P2ymFWA0gan7yHr7Yla05CJnMheL",
    }

    params = {
        "url": link,
        "base64": "1",
        "width": "1366",
        "height": "1024",
    }

    response = requests.get("https://api.apilight.com/screenshot/get", params=params, headers=headers)
    try:
        image_data = base64.b64decode(response.text + "===")  # Padding hatasını düzeltmek için
    except Exception as e:
        return None, str(e)

    image_filename = name

    with open(image_filename, "wb") as image_file:
        image_file.write(image_data)

    return image_filename, None

@Client.on_message(filters.command("ss") & (filters.private | filters.group))
async def screenshot(client, message):
    if len(message.command) < 2:
        await message.reply_text("Lütfen bir link sağlayın. Örnek kullanım: /ss <link>")
        return

    link = message.command[1]
    progress_message = await message.reply_text("Ekran görüntüsü alınıyor...")

    image_filename, error = get_ss(link=link)

    if error:
        await progress_message.edit_text(f"Ekran görüntüsü alınırken bir hata oluştu: {error}")
        return

    await client.send_photo(message.chat.id, image_filename)
    os.remove(image_filename)

    await progress_message.delete()
    await message.delete()

