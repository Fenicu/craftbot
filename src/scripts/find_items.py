import asyncio
import sys

from odmantic import AIOEngine

sys.path.append("/home/fenicu/craftbot/src")

from support.dbmanager.FastMongo import FastOdmanticMongo
from support.models import UserType


async def get_all_items(mongo: AIOEngine):
    users = mongo.find(UserType, UserType.bag.items != [])
    async for user in users:
        for item in user.bag.items:
            if str(item.item_id) == "61b3e64757c00076e647f5c6":
                print(item.count, user.telegram_id)


if __name__ == "__main__":
    mongo = FastOdmanticMongo()
    engine = mongo.get_engine()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_items(engine))
