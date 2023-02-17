import re
from datetime import datetime
from math import ceil
from typing import List

from aiogram import types
from loguru import logger
from odmantic.engine import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.bag_model import BagType
from support.models.items_model import EmbeddedItemType, ItemType


@dp.message_handler(commands=["start", "help"])
@dp.message_handler(text="◀️Назад")
async def starting(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = ["⚒Крафт", "🗜Масс крафт", "🔨Мастерские"]
    if user.admin:
        buttons.append("🖥 Админ Панель")
    kb.add(*buttons)
    out = "Бот помощник при крафте\nКанал с обновлениями — @swcraftupdate"
    await message.answer(out, reply_markup=kb)
    user.fsm = ""
    user.fsm_addons = ""
    await mongo.save(user)


@dp.message_handler(commands=["clear"])
async def starting(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = ["⚒Крафт", "🗜Масс крафт", "🔨Мастерские"]
    if user.admin:
        buttons.append("🖥 Админ Панель")
    kb.add(*buttons)
    user.bag = BagType()
    logger.debug("{}({}) очистил рюкзак", user.name, user.telegram_id)
    await mongo.save(user)
    out = "Инвентарь был очищен"
    await message.answer(out, reply_markup=kb)


@dp.message_handler(regexp="Сделать заказ /myorders")
async def update_bag(message: types.Message, user: UserType, mongo: AIOEngine):
    items: List[EmbeddedItemType] = []
    bag_evaluation = 0
    for line in message.text.splitlines():
        if "Твои ресурсы" in line or "Сделать заказ" in line:
            continue
        if not line:
            continue
        if " - " in line:
            item_info = re.search(r"(?P<item_name>.*) - (?P<item_count>\d+) шт.", line)
            if item := await mongo.find_one(
                ItemType, ItemType.name == item_info.group("item_name")
            ):
                count = int(item_info.group("item_count"))
                bag_evaluation += count * item.evaluation
                items.append(item.short(count=count))
        else:
            if item := await mongo.find_one(ItemType, ItemType.name == line):
                count = 1
                bag_evaluation += count * item.evaluation
                items.append(item.short(count=count))

    user.bag.items = items
    user.bag.last_update = datetime.now()
    await mongo.save(user)
    logger.debug("{}({}) обновил рюкзак", user.name, user.telegram_id)
    kb = types.InlineKeyboardMarkup()
    kb.insert(types.InlineKeyboardButton(text="⚒Крафт", callback_data=f"find_tiers"))
    await message.answer(
        f"Рюкзак был обновлён\nОценка инвентаря: {ceil(bag_evaluation)}🦄",
        reply_markup=kb,
    )
