
import asyncio
from pyrogram import idle

from heda import heda, log
from heda.utils.heroku import heroku


async def main():
    log(__name__).info("Bot starting...")
    await heda.start()
    log(__name__).info("Bot started.")
    print("mrb")
    await heroku()
    await idle()
    log(__name__).info("Bot stopping...")
    await heda.stop()
    log(__name__).info("Bot stopped.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
