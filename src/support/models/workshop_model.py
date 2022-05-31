from datetime import datetime
from enum import Enum
from typing import List

from odmantic import EmbeddedModel, Field, Model
from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine

from support.models.blueprint_model import BlueprintType, TierType


class WorkShopTypes(str, Enum):
    WEAVER = "weaver"
    ENGINEER = "engineer"


WORKSHOP_ICONS = {
    WorkShopTypes.ENGINEER: "⛏",
    WorkShopTypes.WEAVER: "👕",
}


WORKSHOPTYPE_MAPPING = {
    "📱": WorkShopTypes.ENGINEER,
    "⌚️": WorkShopTypes.ENGINEER,
    "💻": WorkShopTypes.ENGINEER,
    "💍": WorkShopTypes.ENGINEER,
    "🕶": WorkShopTypes.WEAVER,
    "👞": WorkShopTypes.WEAVER,
    "👕": WorkShopTypes.WEAVER,
    "👔": WorkShopTypes.WEAVER,
}


class WorkShopBlueprint(EmbeddedModel):
    blueprint_id: ObjectId
    level: int


class WorkShopModel(Model):
    owner: int
    blueprints: List[WorkShopBlueprint] = []
    type: WorkShopTypes
    active: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)

    class Config:
        collection = "workshops"

    @property
    def icon(self) -> str:
        return WORKSHOP_ICONS[self.type]

    async def get_all_tiers(self, mongo: AIOEngine) -> List[int]:
        blueprints = await mongo.find(
            BlueprintType, BlueprintType.id.in_([bp.blueprint_id for bp in self.blueprints])
        )
        tiers_ = await mongo.find(TierType, TierType.id.in_([bp.tier for bp in blueprints]))
        return [tier.tier_id for tier in tiers_]
