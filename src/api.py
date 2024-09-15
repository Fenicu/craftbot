from datetime import datetime
from typing import List

import regex
from fastapi import FastAPI
from pydantic import BaseModel

from support.dbmanager import odmantic_mongo
from support.models.blueprint_model import BlueprintType, SlotType, TierType

engine = odmantic_mongo.get_engine()
app = FastAPI(title="Fenicu Craft Bot API", version="0.1.1")


class Tier(BaseModel):
    tier_id: int
    icon: str = "❓"


class Stats(BaseModel):
    practice: int = 0
    theory: int = 0
    trick: int = 0
    wisdom: int = 0


class Blueprint(BaseModel):
    name: str
    icon: str
    stats: Stats
    tier: Tier
    slot: SlotType
    level: int
    created_at: datetime


def extract_item_data(item_string):
    icon_match = regex.search(r"(\p{So})", item_string)
    icon = icon_match.group(1) if icon_match else None

    name_match = regex.search(r"(?<=\p{So})(.*?)(?=\s*\()", item_string)
    name = name_match.group(1).strip() if name_match else None

    characteristics_matches = regex.findall(r"(\+[\d]+)(\p{So})", item_string)
    characteristics = {}
    for match in characteristics_matches:
        value, char_icon = match
        value = int(value.replace("+", ""))
        char_name = {
            "🔨": "practice",
            "🎓": "theory",
            "🐿": "trick",
            "🐢": "wisdom",
        }.get(char_icon, char_icon)
        characteristics[char_name] = value

    return {"icon": icon, "name": name, "characteristics": characteristics}


@app.get("/blueprints/", response_model=List[Blueprint])
async def get_blueprints():
    bps = await engine.find(BlueprintType)
    result = []
    for bp in bps:
        tier = await engine.find_one(TierType, TierType.id == bp.tier)
        data = extract_item_data(bp.name)
        result.append(
            Blueprint(
                **{
                    "name": data["name"],
                    "icon": data["icon"],
                    "stats": Stats(**data["characteristics"]),
                    "tier": Tier(**{"tier_id": tier.tier_id, "icon": tier.icon}),
                    "slot": bp.slot,
                    "level": bp.level,
                    "created_at": bp.created_at,
                }
            )
        )
    return result
