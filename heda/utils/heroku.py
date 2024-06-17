
import socket
import heroku3

from heda import log
from heda.config import HerokuConfig


HEROKU_APP = None

def is_heroku():
    log(__name__).info(socket.getfqdn())
    return "heroku" in socket.getfqdn()


def heroku():
    global HEROKU_APP
    if is_heroku():
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
            except Exception as e:
                log(__name__).error(str(e))
        else:
            log(__name__).warning(
                "Please make sure your Heroku API Key and Your App name are configured correctly in the heroku."
            )
