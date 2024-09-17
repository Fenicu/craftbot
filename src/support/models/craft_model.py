import json
from datetime import timedelta
from enum import Enum
from math import ceil
from typing import List, Optional, Tuple, Union
from uuid import uuid4

from aiogram import md, types
from aioredis import Redis
from loguru import logger
from odmantic import AIOEngine
from odmantic.bson import ObjectId
from pydantic.main import BaseModel

from support.models.bag_model import BagType
from support.models.blueprint_model import BlueprintType, TierType
from support.models.collections_model import CollectionType
from support.models.items_model import EmbeddedItemType, ItemType
from support.models.user_model import UserType
from support.models.workshop_model import WorkShopModel

COMPLETED = "✅"
NOT_COMPLETED = "❌"
ITEM = "📦"
MONEY = "💧"


class CraftItemModel(BaseModel):
    item_id: str
    needed: int
    available: int


class CraftFilters(str, Enum):
    COMPLITED = "complited"
    NOTCOMPLITED = "notcomplited"
    NOFILTER = "nofilter"
    RAW = "raw"
    RECIPE = "recipe"


class CraftType:
    def __init__(
        self,
        bag: Optional[BagType] = None,
        blueprint: Optional[Union[BlueprintType, List[BlueprintType]]] = None,
        user: Optional[UserType] = None,
    ):
        if all([bag, blueprint]):
            self.bag = bag
            if isinstance(blueprint, BlueprintType):
                blueprint = [blueprint]
            self.blueprints = blueprint
            self.calculate()
        self.user = user

    def calculate(self):
        """
        Расчёт всех необходимых ресурсов в крафте
        """
        self.completed_list: List[CraftItemModel] = []
        self.not_completed_list: List[CraftItemModel] = []

        self.needed_items: List[EmbeddedItemType] = []
        for blueprint in self.blueprints:
            for item_ in blueprint.items:
                for item__ in self.needed_items:
                    if item_.item_id == item__.item_id:
                        item__.count += item_.count
                        break
                else:
                    self.needed_items.append(item_)

        for item_in_blueprint in self.needed_items:
            for item_in_bag in self.bag.items:
                if item_in_blueprint.item_id == item_in_bag.item_id:
                    item = CraftItemModel(
                        item_id=str(item_in_blueprint.item_id),
                        needed=item_in_blueprint.count,
                        available=item_in_bag.count,
                    )
                    if item_in_bag.count >= item_in_blueprint.count:
                        self.completed_list.append(item)
                    else:
                        self.not_completed_list.append(item)
                    break
            else:
                item = CraftItemModel(
                    item_id=str(item_in_blueprint.item_id),
                    needed=item_in_blueprint.count,
                    available=0,
                )
                self.not_completed_list.append(item)

    async def save_craft(self, redis: Redis) -> str:
        """
        Сохранить крафт в базе данных
        """
        craft_id = str(uuid4())
        addr = f"craft:{craft_id}"
        data = {
            "blueprints": [bp.json() for bp in self.blueprints],
            "owner": self.user.json(),
            "completed_list": [item.json() for item in self.completed_list],
            "needed_items": [item.json() for item in self.needed_items],
            "not_completed_list": [item.json() for item in self.not_completed_list],
            "bag_items": [item.json() for item in self.bag.items],
        }
        await redis.set(addr, json.dumps(data), ex=timedelta(weeks=1))
        return craft_id

    async def load_craft(self, redis: Redis, craft_id: str):
        """
        Загрузить крафт из базы данных и рассчитать его
        """
        addr = f"craft:{craft_id}"
        craft = await redis.get(addr)
        if not craft:
            raise ValueError

        craft: dict = json.loads(craft)
        try:
            self.user = UserType.parse_raw(craft["owner"])
            self.blueprints = [
                BlueprintType(**bp) for bp in [json.loads(bp_) for bp_ in craft["blueprints"]]
            ]
            self.completed_list = [
                CraftItemModel(**bp) for bp in [json.loads(bp_) for bp_ in craft["completed_list"]]
            ]
            self.needed_items = [
                EmbeddedItemType(**bp) for bp in [json.loads(bp_) for bp_ in craft["needed_items"]]
            ]
            self.not_completed_list = [
                CraftItemModel(**bp)
                for bp in [json.loads(bp_) for bp_ in craft["not_completed_list"]]
            ]
            self.bag = BagType(items=[json.loads(item) for item in craft["bag_items"]])
        except Exception:
            logger.exception("Ошибочка")
            raise ValueError

    async def filter_keyboard(self, mongo: AIOEngine, craft_id: str) -> types.InlineKeyboardMarkup:
        """
        Получить клавиатуру с фильтрами
        """
        kb = types.InlineKeyboardMarkup(row_width=3)
        url = f"https://t.me/share/url?url=/share {craft_id}"
        buttons = [
            types.InlineKeyboardButton(
                text=COMPLETED,
                callback_data=f"craft:{craft_id}:{CraftFilters.COMPLITED}",
            ),
            types.InlineKeyboardButton(
                text=NOT_COMPLETED,
                callback_data=f"craft:{craft_id}:{CraftFilters.NOTCOMPLITED}",
            ),
            types.InlineKeyboardButton(
                text="Без фильтра",
                callback_data=f"craft:{craft_id}:{CraftFilters.NOFILTER}",
            ),
            types.InlineKeyboardButton(
                text="Импорт", callback_data=f"craft:{craft_id}:{CraftFilters.RAW}"
            ),
            types.InlineKeyboardButton(
                text="Рецепт", callback_data=f"craft:{craft_id}:{CraftFilters.RECIPE}"
            ),
            types.InlineKeyboardButton(text="Поделиться", url=url),
        ]
        if len(self.blueprints) == 1:
            tier = await mongo.find_one(TierType, TierType.id == self.blueprints[0].tier)
            buttons.append(
                types.InlineKeyboardButton(text="◀️Назад", callback_data=f"showtier:{tier.tier_id}")
            )
        kb.add(*buttons)
        return kb

    async def craft_text(
        self,
        mongo: AIOEngine,
        craft_id: str,
        user: Optional[UserType] = None,
        completed_list: bool = True,
        not_completed_list: bool = True,
        raw: bool = False,
        recipe=False,
    ) -> Tuple[str, types.InlineKeyboardMarkup]:
        if user and self.user.telegram_id != user.telegram_id:
            out = f"Владелец крафта: {self.user.name}\n"
        else:
            out = "Крафт:\n"
        if raw:
            for bp in self.blueprints:
                out += f"{md.hbold(bp.name)}\n"
            out += "\n"
            for item_ in self.not_completed_list:
                item = await mongo.find_one(ItemType, ItemType.id == ObjectId(item_.item_id))
                out += f"{item.name} {item_.needed - item_.available}\n{md.hcode(f'/buy_{item.item_id}')} | {md.hcode(f'/sell_{item.item_id}')}\n\n"
            return out, await self.filter_keyboard(mongo, craft_id)

        elif recipe:
            for bp in self.blueprints:
                out += f"{md.hbold(bp.name)}\n"

            out += "\n"
            for item_ in self.needed_items:
                item = await mongo.find_one(ItemType, ItemType.id == ObjectId(item_.item_id))
                out += f"{item.name}: {item_.count}\n"
            return out, await self.filter_keyboard(mongo, craft_id)

        else:
            for bp in self.blueprints:
                out += f"{md.hbold(bp.name)}\n"
            out += "\n"

            if completed_list:
                for item_ in self.completed_list:
                    item = await mongo.find_one(ItemType, ItemType.id == ObjectId(item_.item_id))
                    if item_.available > item_.needed:
                        out += f"{COMPLETED}{item.name} {item_.available}/{item_.needed} ({item_.available - item_.needed}{ITEM})\n"
                    else:
                        out += f"{COMPLETED}{item.name} {item_.available}/{item_.needed}{ITEM}\n"
                out += "\n"

            if not_completed_list:
                for item_ in self.not_completed_list:
                    item = await mongo.find_one(ItemType, ItemType.id == ObjectId(item_.item_id))
                    out += f"{NOT_COMPLETED}{item.name} {item_.available}/{item_.needed}{ITEM} ({item_.needed - item_.available}{ITEM})\n"
                out += "\n"

            craft_evaluation = 0
            for item_ in self.needed_items:
                item = await mongo.find_one(ItemType, ItemType.id == ObjectId(item_.item_id))
                craft_evaluation += item_.count * item.evaluation

            collections_items = {}
            for bp in self.blueprints:
                for coll in bp.collections:
                    for coll_id, item_info in coll.items():
                        if coll_id in collections_items:
                            item_id = list(item_info.keys())[0]
                            item_count = list(item_info.values())[0]
                            if item_id in collections_items[coll_id]:
                                collections_items[coll_id][item_id] += item_count
                            else:
                                collections_items[coll_id][item_id] = item_count
                        else:
                            collections_items[coll_id] = item_info

            if len(collections_items) > 0:
                out += "Предметы для крафта сетов:\n"
                for coll_id, items_info in collections_items.items():
                    collection = await mongo.find_one(
                        CollectionType, CollectionType.id == ObjectId(coll_id)
                    )
                    out += f"{collection.icon}{collection.name}:\n"
                    for item_id, item_count in items_info.items():
                        item_collection = await mongo.find_one(
                            ItemType, ItemType.item_id == int(item_id)
                        )
                        item_in_bag_collection = 0
                        for item_in_bag in self.bag.items:
                            if item_in_bag.item_id == item_collection.id:
                                item_in_bag_collection = item_in_bag.count
                                break
                        out += f"{COMPLETED if item_in_bag_collection >= item_count else NOT_COMPLETED}{item_collection.name} {item_in_bag_collection}/{item_count}\n"
                out += "\n\n"

            out += f"Оценка крафта: {ceil(craft_evaluation)}🦄\n"

            summary = sum([item.count for item in self.needed_items])
            out += f"Предметов: {summary}{ITEM}\n"
            if len(self.blueprints) == 1:
                blueprint = self.blueprints[0]
                crafters_ = await mongo.find(
                    WorkShopModel,
                    WorkShopModel.active == True,
                    sort=WorkShopModel.last_update.desc(),
                )
                crafters: List[WorkShopModel] = []
                for crafter in crafters_:
                    for bp in crafter.blueprints:
                        if bp.blueprint_id == blueprint.id:
                            crafters.append(crafter)
                            break
                if len(crafters) > 0:
                    out += "\nКрафтеры, которые могут скрафтить:\n"
                    for crafter in crafters:
                        owner = await mongo.find_one(
                            UserType,
                            UserType.telegram_id == crafter.owner,
                        )
                        bp_level = 0
                        for bp in crafter.blueprints:
                            if bp.blueprint_id == blueprint.id:
                                bp_level = bp.level
                                break
                        out += md.hlink(
                            owner.name + f" (⚪️{bp_level}-го ур.)" if bp_level > 0 else owner.name,
                            f"https://t.me/share/url?url=/order_{crafter.owner}",
                        )
                        out += "\n"
            return out, await self.filter_keyboard(mongo, craft_id)
