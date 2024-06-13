
from redis.asyncio import Redis

class RedisHandler:
    def __init__(self, url, password):
        self.redis_url = url.split(":")
        self.db = Redis(
            host=self.redis_url[0],
            port=self.redis_url[1],
            password=password,
            decode_responses=True,
        )

    async def is_added(self, var, _id):
        if not str(_id).isdigit():
            return False
        users = await self.get_all(var)
        return str(_id) in users

    async def add_to_db(self, var, _id):
        _id = str(_id)
        if not _id.isdigit():
            return False
        try:
            users = await self.get_all(var)
            users.append(_id)
            await self.db.set(var, self.list_to_str(users))
            return True
        except Exception as e:
            return False

    async def get_all(self, var):
        users = await self.db.get(var)
        return [""] if users is None or users == "" else self.str_to_list(users)

    @staticmethod
    def str_to_list(text):
        return text.split(" ")

    @staticmethod
    def list_to_str(lst):
        return "".join(f"{x} " for x in lst).strip()
