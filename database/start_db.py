from tortoise import Tortoise
from configparser import ConfigParser


class InitializationDB(Tortoise):

    async def run_tortoise(self):
        conf = ConfigParser()
        conf.read("tools/config.ini")
        url = conf["database"]["url"]

        await self.init(db_url=url, modules={'models': ['database.models']})
        await self.generate_schemas()
