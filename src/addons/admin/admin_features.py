import json
from typing import List

from aiogram import md, types
from aioredis import Redis
from odmantic import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.blueprint_model import BlueprintType, TierType
from support.models.collections_model import CollectionType
from support.models.items_model import EmbeddedItemType, ItemType


@dp.message_handler(text="🖥 Админ Панель", global_admin=True)
async def show_panel(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        *[
            "🆕Добавление",
            "🔤Редактирование",
            "Все ресурсы",
            "⚒Последние крафты",
            "◀️Назад",
        ]
    )
    users_count = await mongo.count(UserType)
    users_bags = await mongo.count(UserType, UserType.bag.items != [])
    items_count = await mongo.count(ItemType)
    tier_count = await mongo.count(TierType)
    bp_count = await mongo.count(BlueprintType)
    collect_count = await mongo.count(CollectionType)
    out = "Добро пожаловать в админку!\n\n"
    out += f"В боте {users_count} пользователей, из них {users_bags} обновляли свои рюкзаки\n\n"
    out += f"{md.hbold('Статистика:')}\n"
    out += f"Предметов добавлено: {md.hbold(items_count)}\n"
    out += f"Тиров добавлено: {md.hbold(tier_count)}\n"
    out += f"Рецептов добавлено: {md.hbold(bp_count)}\n"
    out += f"Сетов добавлено: {md.hbold(collect_count)}\n"
    user.fsm = ""
    user.fsm_addons = ""
    await mongo.save(user)
    await message.answer(out, reply_markup=kb)


@dp.message_handler(text="🆕Добавление", global_admin=True)
@dp.message_handler(
    commands="cancel",
    global_admin=True,
    regexp_fsm=r"add_item|add_blueprint|add_tier|add_tier_description|add_collection|add_bp_in_collection",
)
async def show_panel(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        *[
            "Добавить рецепт",
            "Добавить предмет",
            "Добавить тир",
            "Добавить сет",
            "Добавить крафт в сет",
        ]
    )
    kb.row(*["◀️Назад"])
    out = "Добро пожаловать в панель добавления"
    user.fsm = ""
    user.fsm_addons = ""
    await mongo.save(user)
    await message.answer(out, reply_markup=kb)


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


@dp.message_handler(text="⚒Последние крафты", global_admin=True)
async def get_all_items(message: types.Message, redis: Redis):
    keys = await redis.keys("craft:*")
    key_ttl = {}

    for key in keys:
        ttl = await redis.ttl(key)
        key_ttl[key] = ttl

    sorted_keys = sorted(key_ttl.keys(), key=lambda k: key_ttl[k], reverse=True)
    sorted_keys = sorted_keys[:20]

    out = f"Последние {len(sorted_keys)} крафтов:\n\n"
    for key in sorted_keys:
        craft = await redis.get(key)
        craft: dict = json.loads(craft)

        craft_id = key.split(":")[1]
        user = UserType.parse_raw(craft["owner"])
        out += f"{user.mention}: {md.hcode(f'/share {craft_id}')}\n"

    await message.answer(out)
