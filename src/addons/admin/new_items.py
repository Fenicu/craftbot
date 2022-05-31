import re

from aiogram import md, types
from odmantic import AIOEngine

from support.bots import dp
from support.models import UserType
from support.models.blueprint_model import SLOT_MAPPING, BlueprintType, TierType
from support.models.items_model import ItemType


@dp.message_handler(text="🖥 Админ Панель", global_admin=True)
@dp.message_handler(
    commands="cancel",
    global_admin=True,
    regexp_fsm=r"add_item|add_blueprint|add_tier|add_tier_description",
)
async def show_panel(message: types.Message, user: UserType, mongo: AIOEngine):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*["Добавить рецепт", "Добавить предмет", "Добавить тир", "Все ресурсы", "◀️Назад"])
    out = "Добро пожаловать в админку"
    user.fsm = ""
    user.fsm_addons = ""
    await mongo.save(user)
    await message.answer(out, reply_markup=kb)


@dp.message_handler(text="Добавить предмет", global_admin=True)
async def add_item(message: types.Message, user: UserType, mongo: AIOEngine):
    user.fsm = "add_item"
    await mongo.save(user)
    await message.answer(
        f"Введи {md.hcode('item_id - item_name')}\nНапример: {md.hcode('101 - 👔Рваный Костюм')}\n/cancel для отмены"
    )


@dp.message_handler(text="Добавить рецепт", global_admin=True)
async def add_blueprint(message: types.Message, user: UserType, mongo: AIOEngine):
    user.fsm = "add_blueprint"
    await mongo.save(user)
    await message.answer(
        f"Пришли форвард сообщения\n(Заказ для такого-то хуя на такую-то хуйню)\nдоступный у крафторов по команде {md.hcode('/order_NameTier')}\n/cancel для отмены"
    )


@dp.message_handler(text="Добавить тир", global_admin=True)
async def add_tier(message: types.Message, user: UserType, mongo: AIOEngine):
    user.fsm = "add_tier"
    await mongo.save(user)
    await message.answer(
        f"Введи {md.hcode('tier_id - icon')}\nНапример: {md.hcode('11 - 🌞')}\n/cancel для отмены"
    )


@dp.message_handler(my_state="add_item", global_admin=True)
async def create_item(message: types.Message, mongo: AIOEngine):
    item_info = re.search(r"(?P<item_id>\d+) - (?P<item_name>.*)", message.text)
    if not item_info:
        await message.answer(
            "Неверно введена информация о предмете, попробуй ещё раз или нажми /cancel"
        )
        return
    item = ItemType(item_id=int(item_info.group("item_id")), name=item_info.group("item_name"))
    await mongo.save(item)
    await message.answer("Предмет успешно добавлен, добавь ещё или нажми /cancel")


@dp.message_handler(my_state="add_tier", global_admin=True)
async def create_tier(message: types.Message, user: UserType, mongo: AIOEngine):
    tier_info = re.search(r"(?P<tier_id>\d+) - (?P<tier_icon>.*)", message.text)
    if not tier_info:
        await message.answer(
            "Неверно введена информация о тире, попробуй ещё раз или нажми /cancel"
        )
        return
    addon = {"tier_id": int(tier_info.group("tier_id")), "tier_icon": tier_info.group("tier_icon")}
    user.fsm_addons = addon
    user.fsm = "add_tier_description"
    await mongo.save(user)
    await message.answer("А теперь введи описание для тира")


@dp.message_handler(my_state="add_tier_description", global_admin=True)
async def create_tier_description(message: types.Message, user: UserType, mongo: AIOEngine):
    tier = TierType(
        tier_id=user.fsm_addons["tier_id"],
        icon=user.fsm_addons["tier_icon"],
        description=message.text,
    )
    user.fsm = "add_tier"
    user.fsm_addons = ""
    await mongo.save_all([tier, user])
    await message.answer("Новый тир был успешно добавлен, добавь ещё или /cancel")


@dp.message_handler(
    my_state="add_blueprint", global_admin=True, is_forwarded=True, regexp=r"Заказ для"
)
async def create_blueprint(message: types.Message, user: UserType, mongo: AIOEngine):
    text = message.text
    pattern_items = re.compile(
        r"(❌|✅)(?P<item_name>.*) (?P<current_items>\d+)\/(?P<need_items>\d+)"
    )
    pattern_name = re.compile(r"Заказ для .*\nна (?P<item_name>.*)")
    blueprint_name = pattern_name.search(text).group("item_name")
    slot = None
    for slot_ in SLOT_MAPPING:
        if slot_ in blueprint_name:
            slot = SLOT_MAPPING[slot_]
            break
    blueprint_items = pattern_items.findall(text)
    blueprint = await mongo.find_one(BlueprintType, BlueprintType.name == blueprint_name)
    if not blueprint:
        blueprint = BlueprintType(name=blueprint_name, slot=slot)
    for items in blueprint_items:
        if item := await mongo.find_one(ItemType, ItemType.name == items[1]):
            blueprint.items.append(item.short(int(items[3])))
        else:
            await message.answer(f"Не найден предмет: {items[1]}")
            return

    user.fsm_addons = blueprint.id
    user.fsm = "add_blueprint_tier"
    await mongo.save_all([blueprint, user])
    await message.answer("А теперь введи тир предмета")


@dp.message_handler(my_state="add_blueprint_tier", global_admin=True)
async def create_blueprint(message: types.Message, user: UserType, mongo: AIOEngine):
    try:
        tier = int(message.text)
        if tier := await mongo.find_one(TierType, TierType.tier_id == tier):
            blueprint = await mongo.find_one(BlueprintType, BlueprintType.id == user.fsm_addons)
            blueprint.tier = tier.id
            user.fsm_addons = ""
            user.fsm = "add_blueprint"
            await mongo.save_all([blueprint, user])
            await message.answer("Чертёж добавлен, добавь ещё или /cancel")
        else:
            raise ValueError
    except Exception:
        await message.answer("Тир введён неверно, попробуй ещё раз или /cancel")
