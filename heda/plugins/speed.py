from pyrogram import Client, filters
import speedtest

@Client.on_message(filters.command("speed"))
def speed_test(client, message):
    message.reply_text("Speed test is running, please wait...")
    
    st = speedtest.Speedtest()
    st.download()
    st.upload()
    results = st.results.dict()

    download_speed = results["download"] / 1_000_000  # Convert to Mbps
    upload_speed = results["upload"] / 1_000_000      # Convert to Mbps
    ping = results["ping"]
    isp = results["client"]["isp"]

    result_message = (
        f"**Speedtest Results:**\n\n"
        f"**ISP:** {isp}\n"
        f"**Download Speed:** {download_speed:.2f} Mbps\n"
        f"**Upload Speed:** {upload_speed:.2f} Mbps\n"
        f"**Ping:** {ping} ms"
    )

    message.reply_text(result_message)
