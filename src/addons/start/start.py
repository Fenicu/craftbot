import re
from datetime import datetime
from typing import List

from aiogram import types
from odmantic.engine import AIOEngine

from support.bots import dp
from support.models import UserType
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


@dp.message_handler(regexp="Сделать заказ /myorders")
async def update_bag(message: types.Message, user: UserType, mongo: AIOEngine):
    items: List[EmbeddedItemType] = []
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
                items.append(item.short(int(item_info.group("item_count"))))
        else:
            if item := await mongo.find_one(ItemType, ItemType.name == line):
                items.append(item.short(1))

    user.bag.items = items
    user.bag.last_update = datetime.now()
    await mongo.save(user)
    kb = types.InlineKeyboardMarkup()
    kb.insert(types.InlineKeyboardButton(text="⚒Крафт", callback_data=f"find_tiers"))
    await message.answer("Рюкзак был обновлён", reply_markup=kb)
