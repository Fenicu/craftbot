import re
from datetime import datetime, timedelta
from typing import List

from aiogram import types
from aioredis import Redis
from odmantic import AIOEngine
from odmantic.bson import ObjectId

from support.bots import dp
from support.models import UserType
from support.models.blueprint_model import ICON_MAPPING, BlueprintType, TierType
from support.models.craft_model import CraftFilters, CraftType


@dp.message_handler(text="🗜Масс крафт")
async def mass_craft_info(message: types.Message):
    # TODO добавить генерацию случайных команд для разнообразия
    out = """Команда для массового крафта используется так:
<code>/craft t11 chest head t13 legs t12 left right</code>
<code>/craft t16 chest head legs left right</code>
<code>/craft t14 head head head head head</code>
<code>/craft t17 all</code>
После команды craft указывается сначала тир, потом предметы из него, чтобы добавить весь тир, напишите all
Справка по вещам:
📱 - right
⌚️ - left
🕶 - head
👞 - legs
👕 - chest
👔 - torso
💻 - book
💍 - ring
    """
    await message.answer(out)


@dp.message_handler(commands="craft")
async def show_share_craft(
    message: types.Message, user: UserType, mongo: AIOEngine, redis: Redis
):
    mass_craft = message.get_args()
    last_tier = None
    blueprints: List[BlueprintType] = []
    for craft_info in mass_craft.split(" "):
        if tier := re.search(r"t(?P<tier_id>\d+)", craft_info.lower()):
            tier_id = int(tier.group("tier_id"))
            last_tier = await mongo.find_one(TierType, TierType.tier_id == tier_id)
            continue
        if not last_tier:
            continue
        if craft_info.lower() == "all":
            blueprint = await mongo.find(
                BlueprintType, BlueprintType.tier == last_tier.id
            )
            if blueprint:
                blueprints.extend(blueprint)
        else:
            blueprint = await mongo.find_one(
                BlueprintType,
                (BlueprintType.slot == craft_info.lower())
                & (BlueprintType.tier == last_tier.id),
            )
            if blueprint:
                blueprints.append(blueprint)
    if not blueprints:
        await message.answer("Рецепты не найдены")
        return

    craft = CraftType(bag=user.bag, blueprint=blueprints, user=user)
    craft_id = await craft.save_craft(redis)
    text, kb = await craft.craft_text(mongo=mongo, craft_id=craft_id)
    await message.answer(text, reply_markup=kb)


@dp.message_handler(text="⚒Крафт")
async def find_tiers(message: types.Message, user: UserType, mongo: AIOEngine):
    tiers = await mongo.find(TierType)
    if not tiers:
        await message.answer("Чертежей не найдено")
        return
    out = "Выбери тир предметов\n"
    if not user.bag.items:
        out += "⚠️Скинь мне свой /bag"

    elif datetime.now() - user.bag.last_update > timedelta(weeks=1):
        out += "⚠️Ты давно не обновлял свой /bag"

    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for tier in tiers:
        buttons.append(
            types.InlineKeyboardButton(
                text=f"Tier {tier.tier_id}{tier.icon}",
                callback_data=f"showtier:{tier.tier_id}",
            )
        )

    kb.add(*buttons)
    await message.answer(out, reply_markup=kb)


@dp.callback_query_handler(text="find_tiers")
async def find_tier(call: types.CallbackQuery, user: UserType, mongo: AIOEngine):
    tiers = await mongo.find(TierType)
    if not tiers:
        await call.answer("Чертежей не найдено", show_alert=True)
        return
    out = "Выбери тир предметов\n"
    if not user.bag.items:
        out += "⚠️Скинь мне свой /bag"

    elif datetime.now() - user.bag.last_update > timedelta(weeks=1):
        out += "⚠️Ты давно не обновлял свой /bag"

    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for tier in tiers:
        buttons.append(
            types.InlineKeyboardButton(
                text=f"Tier {tier.tier_id}{tier.icon}",
                callback_data=f"showtier:{tier.tier_id}",
            )
        )

    kb.add(*buttons)
    await call.message.edit_text(out, reply_markup=kb)
    await call.answer()


@dp.callback_query_handler(regexp=r"showtier:(?P<tier_id>\d+)")
async def find_tier(call: types.CallbackQuery, regexp: re.Match, mongo: AIOEngine):
    tier_ = int(regexp.group("tier_id"))
    tier = await mongo.find_one(TierType, TierType.tier_id == tier_)
    blueprints = await mongo.find(
        BlueprintType, BlueprintType.tier == tier.id, sort=BlueprintType.slot
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for blueprint in blueprints:
        name = f"{ICON_MAPPING[blueprint.slot]} {blueprint.slot}"
        buttons.append(
            types.InlineKeyboardButton(
                text=name, callback_data=f"showbp:{blueprint.id}"
            )
        )
    kb.add(*buttons)
    kb.row_width = 1
    kb.insert(types.InlineKeyboardButton(text="◀️Назад", callback_data=f"find_tiers"))
    await call.message.edit_text(tier.description, reply_markup=kb)
    await call.answer()


@dp.callback_query_handler(regexp=r"craft:(?P<craft_id>.*):(?P<filter>.*)")
async def load_blueprint(
    call: types.CallbackQuery,
    regexp: re.Match,
    user: UserType,
    mongo: AIOEngine,
    redis: Redis,
):
    craft = CraftType()
    craft_id: str = regexp.group("craft_id")
    try:
        await craft.load_craft(redis=redis, craft_id=craft_id)
    except ValueError:
        await call.answer("Рецепт не найден", show_alert=True)
        return

    craft_filter: str = regexp.group("filter")
    if craft_filter == CraftFilters.COMPLITED:
        text, kb = await craft.craft_text(
            mongo=mongo, user=user, craft_id=craft_id, not_completed_list=False
        )

    elif craft_filter == CraftFilters.NOTCOMPLITED:
        text, kb = await craft.craft_text(
            mongo=mongo, user=user, craft_id=craft_id, completed_list=False
        )

    elif craft_filter == CraftFilters.NOFILTER:
        text, kb = await craft.craft_text(mongo=mongo, user=user, craft_id=craft_id)

    elif craft_filter == CraftFilters.RAW:
        text, kb = await craft.craft_text(
            mongo=mongo, user=user, craft_id=craft_id, raw=True
        )

    elif craft_filter == CraftFilters.RECIPE:
        text, kb = await craft.craft_text(
            mongo=mongo, user=user, craft_id=craft_id, recipe=True
        )

    else:
        await call.answer("Что-то пошло не по плану", show_alert=True)
        return

    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass

    finally:
        await call.answer()


@dp.callback_query_handler(regexp=r"showbp:(?P<blueprint_id>.*)")
async def show_blueprint(
    call: types.CallbackQuery,
    regexp: re.Match,
    user: UserType,
    mongo: AIOEngine,
    redis: Redis,
):
    blueprint = await mongo.find_one(
        BlueprintType, BlueprintType.id == ObjectId(regexp.group("blueprint_id"))
    )
    if not blueprint:
        await call.answer("Такой рецепт не найден", show_alert=True)
        return

    craft = CraftType(bag=user.bag, blueprint=blueprint, user=user)
    craft_id = await craft.save_craft(redis)
    text, kb = await craft.craft_text(mongo=mongo, craft_id=craft_id)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    finally:
        await call.answer()


@dp.message_handler(commands="share")
async def show_share_craft(
    message: types.Message, user: UserType, mongo: AIOEngine, redis: Redis
):
    craft_id = message.get_args()
    craft = CraftType()
    try:
        await craft.load_craft(redis=redis, craft_id=craft_id)
    except ValueError:
        await message.answer("Рецепт не найден")
        return

    text, kb = await craft.craft_text(mongo=mongo, user=user, craft_id=craft_id)
    await message.answer(text, reply_markup=kb)
