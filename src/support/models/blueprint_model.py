from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from bson import ObjectId
from odmantic import Field, Model
from pydantic import BaseModel

from support.models.items_model import EmbeddedItemType

try:
    import ujson as json
except ImportError:
    import json


class SlotType(str, Enum):
    RIGHT = "right"
    LEFT = "left"
    HEAD = "head"
    LEGS = "legs"
    CHEST = "chest"
    TORSO = "torso"
    BOOK = "book"
    RING = "ring"


SLOT_MAPPING = {
    "📱": SlotType.RIGHT,
    "⌚️": SlotType.LEFT,
    "🕶": SlotType.HEAD,
    "👞": SlotType.LEGS,
    "👕": SlotType.CHEST,
    "👔": SlotType.TORSO,
    "💻": SlotType.BOOK,
    "💍": SlotType.RING,
}

ICON_MAPPING = {
    SlotType.RIGHT: "📱",
    SlotType.LEFT: "⌚️",
    SlotType.HEAD: "🕶",
    SlotType.LEGS: "👞",
    SlotType.CHEST: "👕",
    SlotType.TORSO: "👔",
    SlotType.BOOK: "💻",
    SlotType.RING: "💍",
}


class TierType(Model):
    tier_id: int
    icon: str = "❓"
    description: str = "Описания ещё нет"

    def __str__(self) -> str:
        return f"tier_id: {self.tier_id}"


class BlueprintType(Model):
    name: str
    tier: Optional[ObjectId] = None
    slot: SlotType
    items: List[EmbeddedItemType] = []
    collections: List[Dict[str, Dict[str, int]]] = []
    level: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        collection = "blueprints"
        json_loads = json.loads

    def __str__(self) -> str:
        return f"name: {self.name}"
