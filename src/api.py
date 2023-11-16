from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel
from fastapi import FastAPI
from support.dbmanager import odmantic_mongo
from odmantic import AIOEngine

from support.models.blueprint_model import BlueprintType, SlotType, TierType
from support.models.items_model import EmbeddedItemType

engine = odmantic_mongo.get_engine()
app = FastAPI(title="Fenicu Craft Bot API")


class Tier(BaseModel):
    tier_id: int
    icon: str = "❓"


class Blueprint(BaseModel):
    name: str
    tier: Tier
    slot: SlotType
    level: int
    # items: List[EmbeddedItemType] = []
    # collections: List[Dict[str, Dict[str, int]]]
    created_at: datetime


@app.get("/blueprints/", response_model=List[Blueprint])
async def get_blueprints():
    bps = await engine.find(BlueprintType)
    result = []
    for bp in bps:
        tier = await engine.find_one(TierType, TierType.id == bp.tier)
        result.append(
            Blueprint(
                **{
                    "name": bp.name,
                    "tier": Tier(**{"tier_id": tier.tier_id, "icon": tier.icon}),
                    "slot": bp.slot,
                    "level": bp.level,
                    # "items": bp.items,
                    # "collections": bp.collections,
                    "created_at": bp.created_at,
                }
            )
        )
    return result
