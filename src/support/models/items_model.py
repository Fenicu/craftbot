from datetime import datetime

from bson import ObjectId
from odmantic import EmbeddedModel, Field, Model

try:
    import ujson as json
except ImportError:
    import json


class EmbeddedItemType(EmbeddedModel):
    item_id: ObjectId
    count: int = 0

    def __str__(self) -> str:
        return f"item_id: {self.item_id} | need items: {self.count}"


class ItemType(Model):
    item_id: int
    name: str
    evaluation: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        collection = "items"
        json_loads = json.loads

    def short(self, count: int) -> EmbeddedItemType:
        return EmbeddedItemType(item_id=self.id, count=count)

    def __str__(self) -> str:
        return f"item_id: {self.item_id} | item_name: {self.name}"
