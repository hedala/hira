import asyncio
import speedtest
from pyrogram import Client, filters
from pyrogram.types import Message


def testspeed(m: Message):
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        m = m.edit("İndirme hızı hesaplanıyor...")
        test.download()
        m = m.edit("Yükleme hızı hesaplanıyor...")
        test.upload()
        test.results.share()
        result = test.results.dict()
        m = m.edit("Hız testi sonuçlarını paylaşılıyor...")
    except Exception as e:
        return m.edit(e)
    return result


@Client.on_message(
    filters.command("speed")
)
async def speedtest_function(client: Client, message:Message):
    m = await message.reply_text(
        "Yükleme ve indirme hızı kontrol ediliyor..."
    )
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, testspeed, m
    )
    output = f"""**Hızlı Testi Sonuçları**

**Müşteri :**
ISP : `{result['client']['isp']}`
Ülke : `{result['client']['country']}`
  
**Sunucu :**
İsim : `{result['server']['name']}`
Ülke : `{result['server']['country']}, {result['server']['cc']}`
Sponsor : `{result['server']['sponsor']}`
Gecikme : `{result['server']['latency']}`
Ping : `{result['ping']}`
    """
    await client.send_photo(
        chat_id=message.chat.id, 
        photo=result["share"], 
        caption=output
    )
    await m.delete()
