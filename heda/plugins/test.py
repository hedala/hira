from pyrogram import Client, filters
import speedtest


@Client.on_message(filters.command("speedtest"))
async def speedtest_command(client, message):
    await message.reply_text("İnternet hızınızı ölçüyorum, lütfen bekleyin...")

    # Speedtest ölçümünü başlat
    st = speedtest.Speedtest()
    st.download()
    st.upload()
    result = st.results.dict()

    # Sonuçları kullanıcıya gönder
    await message.reply_text(
        f"İnternet Hız Testi Sonuçları:\n\n"
        f"İndirme Hızı: {result['download'] / 1_000_000:.2f} Mbps\n"
        f"Yükleme Hızı: {result['upload'] / 1_000_000:.2f} Mbps\n"
        f"Ping: {result['ping']} ms"
    )
