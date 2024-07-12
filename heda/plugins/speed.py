import speedtest
from pyrogram import Client, filters
from pyrogram.types import Message
from heda import log

@Client.on_message(filters.command(["speed"]))
async def speedtest_command(client: Client, message: Message):
    try:
        await message.reply_text("İnternet hızınız test ediliyor, lütfen bekleyin...")

        st = speedtest.Speedtest()
        st.download()  # Download hızını ölçer
        st.upload()    # Upload hızını ölçer

        download_speed = st.results.download / 1_000_000  # Mbps
        upload_speed = st.results.upload / 1_000_000      # Mbps
        ping = st.results.ping

        speedtest_results = (
            f"İnternet Hız Testi Sonuçları:\n"
            f"📥 İndirme Hızı: {download_speed:.2f} Mbps\n"
            f"📤 Yükleme Hızı: {upload_speed:.2f} Mbps\n"
            f"🏓 Ping: {ping:.2f} ms"
        )

        await message.reply_text(speedtest_results, quote=True)

        log(__name__).info(
            f"Speed test was performed by {message.from_user.full_name}."
        )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text("Bir hata oluştu, lütfen tekrar deneyin.")
