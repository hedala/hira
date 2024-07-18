from pyrogram import Client, filters
from pyrogram.types import Message
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

@Client.on_message(filters.command("ss"))
async def take_screenshot(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("Lütfen geçerli bir bağlantı girin. Örnek: /ss https://www.example.com")
        return

    url = message.command[1]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Web sayfasının içeriğini al
        response = requests.get(url)
        response.raise_for_status()  # HTTP hatalarını kontrol et

        # Sayfa içeriğinden bir resim oluştur
        img = Image.new('RGB', (1200, 630), color='white')
        d = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        # URL'yi resmin üstüne yaz
        d.text((10, 10), f"Screenshot of: {url}", fill='black', font=font)

        # Sayfa içeriğini resme ekle (basit bir şekilde)
        lines = response.text.split('\n')
        y = 50
        for line in lines[:30]:  # İlk 30 satırı al
            d.text((10, y), line[:100], fill='black', font=font)  # Her satırın ilk 100 karakterini al
            y += 20
            if y > 600:
                break

        # Resmi byte dizisine dönüştür
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Resmi kullanıcıya gönder
        await message.reply_photo(img_byte_arr, caption=f"Basit ekran görüntüsü: {url}")

    except requests.RequestException as e:
        await message.reply_text(f"Bağlantı hatası: {str(e)}")
    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {str(e)}")
        print(f"Hata detayları: {e}")  # Konsola daha detaylı hata bilgisi yazdır
