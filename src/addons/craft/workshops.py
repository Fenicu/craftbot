import re
from datetime import datetime
from typing import List

from aiogram import md, types
from loguru import logger
from odmantic import AIOEngine

from support.bots import dp
from support.models.blueprint_model import BlueprintType, TierType
from support.models.user_model import UserType
from support.models.workshop_model import WORKSHOPTYPE_MAPPING, WorkShopBlueprint, WorkShopModel


@dp.message_handler(text="🔨Мастерские")
async def workshop_info(message: types.Message, mongo: AIOEngine):
    workshops = await mongo.find(
        WorkShopModel,
        WorkShopModel.active == True,
        sort=(WorkShopModel.type, WorkShopModel.last_update),
    )
    if not workshops:
        await message.answer("Открытых мастерских сейчас нет")
        return

    out = "Список активных 🔨Мастерских:\n"
    for workshop in workshops:
        tiers = await workshop.get_all_tiers(mongo=mongo)
        owner = await mongo.find_one(UserType, UserType.telegram_id == workshop.owner)
        out += (
            md.hlink(
                f"{workshop.icon} {owner.name} {', '.join([str(tier) for tier in tiers])}",
                f"https://t.me/share/url?url=/order_{workshop.owner}",
            )
            + "\n\n"
        )

    await message.answer(out)


@dp.message_handler(regexp="Что можешь создать", is_forwarded=True)
async def create_workshop(message: types.Message, mongo: AIOEngine, user: UserType):
    pattern = re.compile(
        r"(?P<item_info>.*)\n/craft_(?P<item_slot>right|left|head|legs|chest|torso|book|ring)(?P<item_tier>\d+)",
        re.MULTILINE,
    )
    items = pattern.findall(message.text)
    blueprints: List[WorkShopBlueprint] = []
    ws_type = None
    for item in items:
        tier = await mongo.find_one(TierType, TierType.tier_id == int(item[2]))
        if not tier:
            continue
        blueprint = await mongo.find_one(
            BlueprintType,
            (BlueprintType.slot == item[1]) & (BlueprintType.tier == tier.id),
        )
        if not blueprint:
            continue

        for icon in WORKSHOPTYPE_MAPPING:
            if icon in item[0]:
                ws_type = WORKSHOPTYPE_MAPPING[icon]

        level = re.search(r"(?P<level>\d+)-го", item[0])
        if level:
            level = int(level.group("level"))
        else:
            level = 0

        blueprints.append(WorkShopBlueprint(blueprint_id=blueprint.id, level=level))

    ws = await mongo.find_one(WorkShopModel, WorkShopModel.owner == message.from_user.id)
    if not ws:
        ws = WorkShopModel(
            owner=message.from_user.id,
            blueprints=blueprints,
            type=ws_type,
        )

    else:
        ws.active = True
        ws.blueprints = blueprints
        ws.type = ws_type
        ws.last_update = datetime.now()

    await mongo.save(ws)
    logger.debug("{}({}) обновил лавку", user.name, user.telegram_id)
    await message.answer("Лавка обновлена!")
