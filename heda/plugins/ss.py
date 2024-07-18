from pyrogram import Client, filters
from pyrogram.types import Message
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

@Client.on_message(filters.command("ss"))
async def take_screenshot(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("Lütfen geçerli bir bağlantı girin. Örnek: /ss https://www.example.com")
        return

    url = message.command[1]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Tarayıcı ayarları
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Tarayıcıyı başlat
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        # Sayfayı yükle ve ekran görüntüsü al
        driver.get(url)
        time.sleep(3)  # Sayfanın yüklenmesi için bekle
        screenshot = driver.get_screenshot_as_png()

        # Tarayıcıyı kapat
        driver.quit()

        # Ekran görüntüsünü kaydet
        screenshot_path = f"screenshot_{message.id}.png"
        with open(screenshot_path, "wb") as file:
            file.write(screenshot)

        # Ekran görüntüsünü gönder
        await message.reply_photo(screenshot_path, caption=f"Ekran görüntüsü: {url}")

        # Dosyayı sil
        os.remove(screenshot_path)

    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {str(e)}")
