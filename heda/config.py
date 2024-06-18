
import os
from pathlib import Path
from dotenv import load_dotenv


def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % val)


load_dotenv()


class BotConfig:
    BOT_NAME = str(os.getenv("BOT_NAME"))
    API_ID = int(os.getenv("API_ID"))
    API_HASH = str(os.getenv("API_HASH"))
    BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

class LogConfig:
    DEBUG = strtobool(os.getenv("DEBUG"))
    LOG_TO_FILE = strtobool(os.getenv("LOG_TO_FILE"))
    LOG_FILE_PATH = Path(os.getenv("LOG_FILE_PATH"))
    LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID"))

class DbConfig:
    REDIS_URL = str(os.environ.get("REDIS_URL"))
    REDIS_PASSWORD = str(os.environ.get("REDIS_PASSWORD"))

class DataConfig:
    OWNER_ID = int(os.getenv("OWNER_ID"))

class HerokuConfig:
    HEROKU_API_KEY = str(os.getenv("HEROKU_API_KEY"))
    HEROKU_APP_NAME = str(os.getenv("HEROKU_APP_NAME"))
    UPSTREAM_BRANCH = str(os.getenv("UPSTREAM_BRANCH"))
    UPSTREAM_REPO = str(os.getenv("UPSTREAM_REPO"))
    GIT_TOKEN = str(os.getenv("GIT_TOKEN"))
