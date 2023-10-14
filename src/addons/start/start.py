import re
from datetime import datetime
from math import ceil
from typing import List

from aiogram import md, types
from bson import ObjectId
from loguru import logger
from odmantic.engine import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.bag_model import BagType
from support.models.group import GroupType
from support.models.items_model import EmbeddedItemType, ItemType
from support.models.users_in_groups import UserInGroupType


@dp.message_handler(commands=["start", "help"])
@dp.message_handler(text="◀️Назад")
async def starting(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = ["⚒Крафт", "🗜Масс крафт", "🔨Мастерские", "🚼Группы"]
    if user.admin:
        buttons.append("🖥 Админ Панель")
    kb.add(*buttons)
    out = "Бот помощник при крафте\nКанал с обновлениями — @swcraftupdate"
    await message.answer(out, reply_markup=kb)
    user.fsm = ""
    user.fsm_addons = ""
    await mongo.save(user)


@dp.message_handler(commands=["clear"])
async def clear_bag(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = ["⚒Крафт", "🗜Масс крафт", "🔨Мастерские", "🚼Группы"]
    if user.admin:
        buttons.append("🖥 Админ Панель")
    kb.add(*buttons)
    user.bag = BagType()
    logger.debug("{}({}) очистил рюкзак", user.name, user.telegram_id)
    await mongo.save(user)
    out = "Инвентарь был очищен"
    await message.answer(out, reply_markup=kb)


async def get_diff(
    old_items: List[EmbeddedItemType],
    new_items: List[EmbeddedItemType],
    mongo: AIOEngine,
) -> str:
    text = "Изменения в инвентаре:\n\n"
    for oitem in old_items:
        item = await mongo.find_one(ItemType, ItemType.id == oitem.item_id)
        for nitem in new_items:
            if nitem.item_id == oitem.item_id:
                break
        else:
            text += f"🔴 {item.name} -{oitem.count}\n"
            continue

        if nitem.count > oitem.count:
            text += f"🟢 {item.name} +{nitem.count-oitem.count}\n"
        elif nitem.count < oitem.count:
            text += f"🔴 {item.name} -{oitem.count-nitem.count}\n"
        continue

    return text


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

    old_items = user.bag.items.copy()
    user.bag.items = items
    current_items = user.bag.items.copy()
    diff_message = await get_diff(old_items, current_items, mongo)
    diff_date = user.bag.last_update
    user.bag.last_update = datetime.now()
    await mongo.save(user)
    logger.debug("{}({}) обновил рюкзак", user.name, user.telegram_id)
    kb = types.InlineKeyboardMarkup()
    kb.insert(types.InlineKeyboardButton(text="⚒Крафт", callback_data=f"find_tiers"))
    await message.answer(
        f"Рюкзак был обновлён\nОценка инвентаря: {ceil(bag_evaluation)}🦄\n{diff_message}\nСравнение от {diff_date.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=kb,
    )


@dp.message_handler(text="🚼Группы", global_admin=True)
async def show_groups(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*["Мои группы", "Создать группу", "◀️Назад"])

    out = "В группах ты можешь просматривать рюкзаки товарищей"
    await message.answer(out, reply_markup=kb)


@dp.message_handler(text="Создать группу")
async def create_group(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["◀️Назад"]
    kb.add(*buttons)
    user.fsm = "set_group_name"
    await mongo.save(user)
    out = "Дай имя группе"
    await message.answer(out, reply_markup=kb)


@dp.message_handler(my_state="set_group_name")
async def set_group_name(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*["Мои группы", "Создать группу", "◀️Назад"])
    user.fsm = ""
    group = GroupType(owner=message.from_user.id, name=message.text)
    new_group = await mongo.save(group)
    add_user_in_group = UserInGroupType(group=new_group.id, user=message.from_user.id)
    await mongo.save_all([user, add_user_in_group])
    out = f"Команда для вступления пользователей:\n{md.hcode(new_group.join_command)}"
    await message.answer(out, reply_markup=kb)


@dp.message_handler(commands=["join"])
async def join_group(message: types.Message, mongo: AIOEngine):
    try:
        group_id = ObjectId(message.get_args())
        group = await mongo.find_one(GroupType, GroupType.id == group_id)
        if not group:
            await message.answer("Такой группы не найдено")
            return
        user_in_group = await mongo.find_one(
            UserInGroupType,
            UserInGroupType.group == group_id,
            UserInGroupType.user == message.from_user.id,
        )
        if user_in_group:
            await message.answer("Ты уже состоишь в группе")
            return
    except Exception:
        pass

    add_user_in_group = UserInGroupType(group=group.id, user=message.from_user.id)
    await mongo.save(add_user_in_group)

    await message.answer(f"Ты успешно вступил в группу {group.name}")


@dp.message_handler(text="Мои группы", global_admin=True)
async def show_groups(message: types.Message, mongo: AIOEngine):
    user_groups = await mongo.find(
        UserInGroupType,
        UserInGroupType.user == message.from_user.id,
    )
    ids = [g.id for g in user_groups]
    user_group = await mongo.find(GroupType, GroupType.id in ids)
    # TODO
