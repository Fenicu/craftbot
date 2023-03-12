from typing import List

from aiogram import md, types
from odmantic import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.items_model import EmbeddedItemType, ItemType


@dp.message_handler(text="Все ресурсы", global_admin=True)
async def get_all_items(message: types.Message, mongo: AIOEngine):
    users = mongo.find(UserType, UserType.bag.items != [])
    all_items: List[EmbeddedItemType] = []
    async for user in users:
        for item in user.bag.items:
            for item_ in all_items:
                if item_.item_id == item.item_id:
                    item_.count += item.count
                    break
            else:
                all_items.append(item)

    all_items = sorted(all_items, key=lambda item: item.count, reverse=True)
    count = await mongo.count(UserType, UserType.bag.items != [])
    out = f"Количество предметов на руках у {count} игроков:\n"
    for item in all_items:
        item_obj = await mongo.find_one(ItemType, ItemType.id == item.item_id)
        out += f"{md.hbold(item_obj.name)}: {item.count} ({round(item_obj.evaluation, 3)} 🦄)\n"

    await message.answer(out)
