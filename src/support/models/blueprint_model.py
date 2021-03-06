from datetime import datetime
from enum import Enum
from typing import List, Optional

from bson import ObjectId
from odmantic import Field, Model

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
    "π±": SlotType.RIGHT,
    "βοΈ": SlotType.LEFT,
    "πΆ": SlotType.HEAD,
    "π": SlotType.LEGS,
    "π": SlotType.CHEST,
    "π": SlotType.TORSO,
    "π»": SlotType.BOOK,
    "π": SlotType.RING,
}

ICON_MAPPING = {
    SlotType.RIGHT: "π±",
    SlotType.LEFT: "βοΈ",
    SlotType.HEAD: "πΆ",
    SlotType.LEGS: "π",
    SlotType.CHEST: "π",
    SlotType.TORSO: "π",
    SlotType.BOOK: "π»",
    SlotType.RING: "π",
}


class TierType(Model):
    tier_id: int
    icon: str = "β"
    description: str = "ΠΠΏΠΈΡΠ°Π½ΠΈΡ Π΅ΡΡ Π½Π΅Ρ"

    def __str__(self) -> str:
        return f"tier_id: {self.tier_id}"


class BlueprintType(Model):
    name: str
    tier: Optional[ObjectId] = None
    slot: SlotType
    items: List[EmbeddedItemType] = []
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        collection = "blueprints"
        json_loads = json.loads

    def __str__(self) -> str:
        return f"name: {self.name} | tier: {self.tier}"
