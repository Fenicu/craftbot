import asyncio
import sys
from typing import List

from odmantic import AIOEngine

sys.path.append("/home/fenicu/craftbot/src")

from support.dbmanager.FastMongo import FastOdmanticMongo
from support.models import UserType
from support.models.blueprint_model import BlueprintType, TierType
from support.models.items_model import EmbeddedItemType, ItemType


async def get_all_items(mongo: AIOEngine):
    users = mongo.find(UserType, UserType.bag.items != [])
    all_items: List[EmbeddedItemType] = []
    async for user in users:
        for item in user.bag.items:
            item: EmbeddedItemType
            for item_ in all_items:
                if item.item_id == item_.item_id:
                    item_.count += item.count
                    break
            else:
                all_items.append(item)

    best_tier = await mongo.find_one(TierType, sort=TierType.tier_id.desc())
    crafts_in_tier = mongo.find(BlueprintType, BlueprintType.tier == best_tier.id)
    items_in_craft: List[EmbeddedItemType] = []
    async for craft in crafts_in_tier:
        for item in craft.items:
            for item_ in items_in_craft:
                if item.item_id == item_.item_id:
                    item_.count += item.count
                    break
            else:
                items_in_craft.append(item)

    items = []
    for item in all_items:
        for needed_item in items_in_craft:
            if needed_item.item_id == item.item_id:
                item_obj = await mongo.find_one(ItemType, ItemType.id == item.item_id)
                item_obj.evaluation = needed_item.count / item.count
                items.append(item_obj)
                break

    await mongo.save_all(items)


if __name__ == "__main__":
    mongo = FastOdmanticMongo()
    engine = mongo.get_engine()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_items(engine))
