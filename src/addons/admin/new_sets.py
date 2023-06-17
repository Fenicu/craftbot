import re

from aiogram import md, types
from loguru import logger
from odmantic import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.blueprint_model import SLOT_MAPPING, BlueprintType, TierType
from support.models.collections_model import CollectionType
from support.models.items_model import ItemType


@dp.message_handler(text="Добавить сет", global_admin=True)
async def add_collection(message: types.Message, user: UserType, mongo: AIOEngine):
    user.fsm = "add_collection"
    await mongo.save(user)
    await message.answer(
        f"Введи {md.hcode('collection_icon - collection_name')}\nНапример: {md.hcode('🧸 - Соня')}\n/cancel для отмены"
    )


@dp.message_handler(text="Добавить крафт в сет", global_admin=True)
async def add_bp_in_collection(message: types.Message, user: UserType, mongo: AIOEngine):
    user.fsm = "add_bp_in_collection"
    await mongo.save(user)
    await message.answer(
        f"Введи {md.hcode('set_icon:tier_id:slot:item_id:item_count')}\nНапример: {md.hcode('🧸:18:right:118:15')}\n\n"
        "Это значит, что мы добавим 📱iBlackM (+57🔨, +29🎓) (18 тир, слот right) в сет 🧸Соня"
        " и для крафта ему надо 15 💽Прошивка\n\n"
        "Справка по вещам:\n"
        f"📱 - {md.hcode('right')}\n"
        f"⌚️ - {md.hcode('left')}\n"
        f"🕶 - {md.hcode('head')}\n"
        f"👞 - {md.hcode('legs')}\n"
        f"👕 - {md.hcode('chest')}\n"
        f"👔 - {md.hcode('torso')}\n"
        f"💻 - {md.hcode('book')}\n"
        f"💍 - {md.hcode('ring')}\n\n"
        f"💎 - {md.hcode('117')}\n"
        f"💽 - {md.hcode('118')}\n"
        f"🧶 - {md.hcode('107')}\n"
        f"📿 - {md.hcode('108')}\n"
        "\n\n/cancel для отмены"
    )


@dp.message_handler(my_state="add_bp_in_collection", global_admin=True)
async def create_bp_in_collection(message: types.Message, mongo: AIOEngine):
    item_info = re.search(
        r"(?P<set_icon>.*):(?P<tier_id>\d+):(?P<slot>.*):(?P<item_id>\d+):(?P<item_count>\d+)",
        message.text,
    )
    if not item_info:
        await message.answer(
            "Неверно введена информация о сете, попробуй ещё раз или нажми /cancel"
        )
        return
    tier = await mongo.find_one(TierType, TierType.tier_id == int(item_info.group("tier_id")))
    if not tier:
        await message.answer(
            f"Тир {item_info.group('tier_id')} не найден, попробуй ещё раз или нажми /cancel"
        )
        return
    bp = await mongo.find_one(
        BlueprintType,
        (BlueprintType.tier == tier.id) & (BlueprintType.slot == item_info.group("slot")),
    )
    if not bp:
        await message.answer("Такой крафт не найден, попробуй ещё раз или нажми /cancel")
        return

    collection = await mongo.find_one(
        CollectionType,
        CollectionType.icon == item_info.group("set_icon"),
    )
    if not collection:
        await message.answer(
            f"Сет {item_info.group('set_icon')} не найден, попробуй ещё раз или нажми /cancel"
        )
        return

    item = await mongo.find_one(ItemType, ItemType.item_id == int(item_info.group("item_id")))
    if not item:
        await message.answer(
            f"Предмет {item_info.group('item_id')} не найден, попробуй ещё раз или нажми /cancel"
        )
        return

    data = {str(collection.id): {str(item.item_id): int(item_info.group("item_count"))}}
    bp.collections.append(data)
    await mongo.save(bp)
    await message.answer(
        f"В крафт {bp.name} добавлено {item.name} {item_info.group('item_count')}шт. для сета {collection.icon}{collection.name}\n\nдобавь ещё или нажми /cancel"
    )


@dp.message_handler(my_state="add_collection", global_admin=True)
async def create_collection(message: types.Message, mongo: AIOEngine):
    item_info = re.search(r"(?P<collection_icon>.*) - (?P<collection_name>.*)", message.text)
    if not item_info:
        await message.answer(
            "Неверно введена информация о сете, попробуй ещё раз или нажми /cancel"
        )
        return
    collection = CollectionType(
        icon=item_info.group("collection_icon"),
        name=item_info.group("collection_name"),
    )
    await mongo.save(collection)
    await message.answer("Сет успешно добавлен, добавь ещё или нажми /cancel")
