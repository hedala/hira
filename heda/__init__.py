
from pyrogram import Client, enums

from heda.config import BotConfig, DbConfig
from heda.utils.paste import Paste
from heda.utils.logging import log
from heda.database.redis_db import RedisHandler


VERSION = "1.1.4"

log = log

paste = Paste()

heda: Client = Client(
    name=BotConfig.BOT_NAME,
    api_id=BotConfig.API_ID,
    api_hash=BotConfig.API_HASH,
    bot_token=BotConfig.BOT_TOKEN,
    parse_mode=enums.ParseMode.MARKDOWN,
    plugins=dict(root="heda.plugins")
)

redis = RedisHandler(
    DbConfig.REDIS_URL,
    DbConfig.REDIS_PASSWORD
)
