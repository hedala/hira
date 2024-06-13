
import socket
import heroku3

from heda import log
from heda.config import HerokuConfig


HEROKU_APP = None

async def is_heroku():
    return "heroku" in socket.getfqdn()


async def heroku():
    global HEROKU_APP
    if await is_heroku():
        if HerokuConfig.HEROKU_API_KEY and HerokuConfig.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(
                    HerokuConfig.HEROKU_API_KEY
                )
                HEROKU_APP = Heroku.app(
                    HerokuConfig.HEROKU_APP_NAME
                )
                log(__name__).info(
                    "Heroku App configured."
                )
            except BaseException:
                log(__name__).warning(
                    "Please make sure your Heroku API Key and Your App name are configured correctly in the heroku."
                )
