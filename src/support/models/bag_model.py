from datetime import datetime
from typing import List

from odmantic import EmbeddedModel, Field

from support.models.items_model import EmbeddedItemType


class BagType(EmbeddedModel):
    items: List[EmbeddedItemType] = []
    last_update: datetime = Field(default_factory=datetime.now)
