
import os
from pathlib import Path
from dotenv import load_dotenv


vars_ = {
    "BOT_NAME": "str",
    "API_ID": "int",
    "API_HASH": "str",
    "BOT_TOKEN": "str",
    "DEBUG": "bool",
    "LOG_TO_FILE": "bool",
    "LOG_FILE_PATH": "Path",
    "LOG_CHAT_ID": "int",
    "REDIS_URL": "str",
    "REDIS_PASSWORD": "str",
    "OWNER_ID": "int",
    "HEROKU_API_KEY": "str",
    "HEROKU_APP_NAME": "str",
    "UPSTREAM_BRANCH": "str",
    "UPSTREAM_REPO": "str",
    "GIT_TOKEN": "str"
}


def make_config():
    with open("config.env", "a") as file:
        for var in vars_:
            type_ = vars_[var]
            inp = input(f"Enter {var} ({type_})\n: ")
            file.write(f'{var}="{inp}"\n')
    from heda import log
    log(__name__).info(
        "Successfully created config.env file..."
    )

def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % val)

"""
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    make_config()
    load_dotenv("config.env")
"""
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
