from datetime import datetime, timedelta
from math import ceil
from typing import List, Tuple

from aiogram import md, types
from odmantic import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.items_model import ItemType


async def calculate_bag_value(user: UserType, mongo: AIOEngine) -> float:
    total_value = 0.0
    item_ids = [item_in_bag.item_id for item_in_bag in user.bag.items]

    items = await mongo.find(ItemType, ItemType.id.in_(item_ids))

    items_dict = {item.id: item for item in items}

    for item_in_bag in user.bag.items:
        item = items_dict.get(item_in_bag.item_id)
        if item:
            total_value += item_in_bag.count * item.evaluation

    return total_value


async def get_top_users_with_values(
    mongo: AIOEngine, limit: int = 100
) -> List[Tuple[UserType, float]]:
    date = datetime.now() - timedelta(weeks=52)
    users = await mongo.find(
        UserType,
        UserType.bag.items != [],
        UserType.bag.last_update >= date,
        sort=UserType.bag.last_update.desc(),
    )

    if not users:
        return []

    all_item_ids = set()
    for user in users:
        for item_in_bag in user.bag.items:
            all_item_ids.add(item_in_bag.item_id)

    items = await mongo.find(ItemType, ItemType.id.in_(list(all_item_ids)))
    items_dict = {item.id: item for item in items}

    user_values = []
    for user in users:
        total_value = 0.0
        for item_in_bag in user.bag.items:
            item = items_dict.get(item_in_bag.item_id)
            if item and item.evaluation > 0:
                total_value += item_in_bag.count * item.evaluation

        if total_value > 0:
            user_values.append((user, total_value))

    user_values.sort(key=lambda x: x[1], reverse=True)

    return user_values[:limit]


@dp.message_handler(commands=["top"])
async def show_rating(message: types.Message, user: UserType, mongo: AIOEngine):
    user_values = await get_top_users_with_values(mongo, limit=100)

    if not user_values:
        await message.answer("Рейтинг пока пуст. Обнови свой рюкзак командой /bag")
        return

    user_position = None
    user_value = 0.0

    for i, (u, value) in enumerate(user_values):
        if u.telegram_id == user.telegram_id:
            user_position = i + 1
            user_value = value
            break

    if user_position is None:
        user_value = await calculate_bag_value(user, mongo)
        if user_value > 0:
            for i, (u, value) in enumerate(user_values):
                if user_value >= value:
                    user_position = i + 1
                    break
            else:
                user_position = len(user_values) + 1

    out = "🏆 <b>Твой рейтинг по стоимости рюкзака:</b>\n\n"

    if user_position and user_value > 0:
        out += f"Твоя позиция: <b>#{user_position}</b> из {len(user_values)}\n"
        out += f"Стоимость твоего рюкзака: <b>{ceil(user_value)}🦄</b>\n\n"
    else:
        out += "Ты пока не в рейтинге. Обнови свой рюкзак командой /bag\n\n"

    out += "<b>Топ-10 игроков:</b>\n"

    start_index = 0
    end_index = min(10, len(user_values))

    if user_position and user_position <= 10:
        start_index = max(0, user_position - 6)
        end_index = min(len(user_values), user_position + 5)
    elif user_position and user_position <= len(user_values):
        start_index = 0
        end_index = min(5, len(user_values))

    for i in range(start_index, end_index):
        u, value = user_values[i]
        position = i + 1

        if u.telegram_id == user.telegram_id:
            out += f"<b>{position}. {md.hbold(u.name)} - {ceil(value)}🦄</b> 👈 Это ты!\n"
        else:
            out += f"{position}. {md.hitalic('<hidden>')} - {ceil(value)}🦄\n"

    if user_position and user_position > end_index:
        out += "...\n"
        out += f"<b>{user_position}. {md.hbold(user.name)} - {ceil(user_value)}🦄</b> 👈 Это ты!\n"

    if len(user_values) > 10:
        out += "...\n"
        last_start = max(10, len(user_values) - 3)
        for i in range(last_start, len(user_values)):
            u, value = user_values[i]
            position = i + 1

            if u.telegram_id == user.telegram_id:
                out += f"<b>{position}. {md.hbold(u.name)} - {ceil(value)}🦄</b> 👈 Это ты!\n"
            else:
                out += f"{position}. {md.hitalic('<hidden>')} - {ceil(value)}🦄\n"

    await message.answer(out, parse_mode="HTML")
