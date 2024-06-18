from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import aiohttp
from json import loads
from heda import log

@Client.on_message(filters.command(["wh"]))
async def handle_weather_command(client: Client, message: Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("Lütfen bir konum girin. 🌍")
        return

    location = command_parts[1]

    try:
        weather_info = await get_wttr_mgm(location)
        if weather_info:
            await message.reply_text(weather_info)
        else:
            await message.reply_text("Hava durumu bilgisi alınamadı. ❌")
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name} for location {location}."
        )
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

@Client.on_message(filters.command(["whall"]))
async def handle_all_weather_command(client: Client, message: Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("Lütfen bir şehir girin. 🌍")
        return

    il = command_parts[1].capitalize()

    try:
        weather_info = await get_all_districts_weather(il)
        if weather_info:
            await message.reply_text(weather_info)
        else:
            await message.reply_text("İlçelerin hava durumu bilgisi alınamadı. ❌")
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name} for city {il}."
        )
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

async def get_wttr_mgm(location: str):
    mgm_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0 Win64 x64 rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr,en-US;q=0.7,en;q=0.3",
        "Referer": "https://mgm.gov.tr/",
        "Origin": "https://mgm.gov.tr",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "Priority": "u=1",
    }

    query_location = requests.get(
        f"https://servis.mgm.gov.tr/web/merkezler?sorgu={location}&limit=50",
        headers=mgm_headers,
    )

    if query_location.status_code >= 400:
        return None

    location_result = loads(query_location.text)
    if not len(location_result):
        return None

    first_location = location_result[0]
    first_center_id = first_location["merkezId"]

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://servis.mgm.gov.tr/web/sondurumlar?merkezid={first_center_id}",
            headers=mgm_headers,
        ) as query_weather:
            if query_weather.status >= 400:
                return None

            weather_result = await query_weather.json()
            if not len(weather_result):
                return None

            status = convert_mgm_status_code(weather_result[0]["hadiseKodu"])

            def get_city_state_mgm():
                if "ilce" in first_location:
                    return f"{first_location['ilce']} / {first_location['il']}"
                return first_location["il"]

            city_state = get_city_state_mgm()
            temp = weather_result[0]["sicaklik"]
            temp_water = weather_result[0].get("denizSicaklik", None)
            wind_speed = int(weather_result[0]["ruzgarHiz"])
            humidity = weather_result[0]["nem"]
            pressure = weather_result[0]["denizeIndirgenmisBasinc"]

            weather_report = (
                f"🌆 {city_state} için Hava Durumu:\n"
                f"📋 Durum: {status}\n"
                f"🌡️ Sıcaklık: {temp}°C\n"
            )
            if temp_water is not None and temp_water != -9999:
                weather_report += f"🌊 Deniz Sıcaklığı: {temp_water}°C\n"
            weather_report += (
                f"💨 Rüzgar Hızı: {wind_speed} km/h\n"
                f"💧 Nem: {humidity}%\n"
                f"🔴 Basınç: {pressure} hPa"
            )

            return weather_report

async def get_all_districts_weather(il: str):
    mgm_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0 Win64 x64 rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr,en-US;q=0.7,en;q=0.3",
        "Referer": "https://mgm.gov.tr/",
        "Origin": "https://mgm.gov.tr",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "Priority": "u=1",
    }

    query_location = requests.get(
        f"https://servis.mgm.gov.tr/web/merkezler?sorgu={il}&limit=50",
        headers=mgm_headers,
    )

    if query_location.status_code >= 400:
        return None

    location_result = loads(query_location.text)
    if not len(location_result):
        return None

    districts_weather = []

    async with aiohttp.ClientSession() as session:
        for location in location_result:
            center_id = location["merkezId"]
            async with session.get(
                f"https://servis.mgm.gov.tr/web/sondurumlar?merkezid={center_id}",
                headers=mgm_headers,
            ) as query_weather:
                if query_weather.status >= 400:
                    continue

                weather_result = await query_weather.json()
                if not len(weather_result):
                    continue

                district = location['ilce'] if "ilce" in location else location["il"]
                temp = weather_result[0]["sicaklik"]

                districts_weather.append(f"{district}: {temp}°C")

    if districts_weather:
        return f"🌆 {il} İline Bağlı İlçelerin Sıcaklık Değerleri:\n" + "\n".join(districts_weather)
    return None

def convert_mgm_status_code(status: str):
    match status:
        case "A":
            return "Açık ☀️"
        case "AB":
            return "Az Bulutlu 🌤️"
        case "PB":
            return "Parçalı Bulutlu ⛅"
        case "CB":
            return "Çok Bulutlu ☁️"
        case "HY":
            return "Hafif Yağmurlu 🌦️"
        case "Y":
            return "Yağmurlu 🌧️"
        case "KY":
            return "Kuvvetli Yağmurlu 🌧️"
        case "KKY":
            return "Karla Karışık Yağmurlu 🌨️"
        case "HKY":
            return "Hafif Kar Yağışlı ❄️"
        case "K":
            return "Kar Yağışlı ❄️"
        case "YKY":
            return "Yoğun Kar Yağışlı ❄️"
        case "HSY":
            return "Hafif Sağanak Yağışlı 🌦️"
        case "SY":
            return "Sağanak Yağışlı 🌧️"
        case "KSY":
            return "Kuvvetli Sağanak Yağışlı 🌧️"
        case "MSY":
            return "Mevzi Sağanak Yağışlı 🌦️"
        case "DY":
            return "Dolu 🌩️"
        case "GSY":
            return "Gökgürültülü Sağanak Yağışlı ⛈️"
        case "KGY":
            return "Kuvvetli Gökgürültülü Sağanak Yağışlı ⛈️"
        case "SIS":
            return "Sisli 🌫️"
        case "PUS":
            return "Puslu 🌫️"
        case "DMN":
            return "Dumanlı 🌫️"
        case "KF":
            return "Kum veya Toz Taşınımı 🌪️"
        case "R":
            return "Rüzgarlı 💨"
        case "GKR":
            return "Güneyli Kuvvetli Rüzgar 🌬️"
        case "KKR":
            return "Kuzeyli Kuvvetli Rüzgar 🌬️"
        case "SCK":
            return "Sıcak 🔥"
        case "SGK":
            return "Soğuk ❄️"
        case "HHY":
            return "Yağışlı 🌧️"
        case _:
            return status
