import asyncio
import sys

from odmantic import AIOEngine

sys.path.append("/home/fenicu/craftbot/src")
from support.dbmanager.FastMongo import FastOdmanticMongo
from support.models.blueprint_model import BlueprintType, TierType

icon_to_level = {
    "🌞": {
        "book": 35,
        "ring": 35,
        "left": 38,
        "right": 38,
        "head": 39,
        "legs": 39,
        "chest": 40,
        "torso": 40,
    },
    "🍂": {
        "book": 39,
        "ring": 39,
        "left": 41,
        "right": 41,
        "head": 42,
        "legs": 42,
        "chest": 43,
        "torso": 43,
    },
    "❄️": {
        "book": 42,
        "ring": 42,
        "left": 44,
        "right": 44,
        "head": 45,
        "legs": 45,
        "chest": 46,
        "torso": 46,
    },
    "🐷": {
        "book": 45,
        "ring": 45,
        "left": 47,
        "right": 47,
        "head": 48,
        "legs": 48,
        "chest": 49,
        "torso": 49,
    },
    "🆘": {
        "book": 45,
        "ring": 45,
        "left": 47,
        "right": 47,
        "head": 48,
        "legs": 48,
        "chest": 49,
        "torso": 49,
    },
    "🌸": {
        "book": 48,
        "ring": 48,
        "left": 50,
        "right": 50,
        "head": 51,
        "legs": 51,
        "chest": 52,
        "torso": 52,
    },
    "🗳": {
        "book": 51,
        "ring": 51,
        "left": 53,
        "right": 53,
        "head": 54,
        "legs": 54,
        "chest": 55,
        "torso": 55,
    },
    "🧸 🧑‍🍳 🗺 📖": {
        "book": 54,
        "ring": 54,
        "left": 56,
        "right": 56,
        "head": 57,
        "legs": 57,
        "chest": 58,
        "torso": 58,
    },
}


async def get_all_items(mongo: AIOEngine):
    bps = mongo.find(BlueprintType)
    async for bp in bps:
        tier = await engine.find_one(TierType, TierType.id == bp.tier)
        bp.level = icon_to_level[tier.icon][bp.slot]
        await mongo.save(bp)


if __name__ == "__main__":
    mongo = FastOdmanticMongo()
    engine = mongo.get_engine()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_items(engine))
