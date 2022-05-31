from datetime import datetime
from typing import Any, Optional

from aiogram import md
from odmantic import Field, Model

from support.models.bag_model import BagType

try:
    import ujson as json
except ImportError:
    import json


class UserType(Model):
    """
    Модель пользователя
    """

    telegram_id: int = Field(primary_field=True)
    name: str
    username: Optional[str] = None
    language: str = "ru"
    admin: bool = False
    ban: bool = False
    fsm: str = ""
    bag: BagType = BagType()
    created_at: datetime = Field(default_factory=datetime.now)
    fsm_addons: Any = ""

    class Config:
        collection = "users"
        json_loads = json.loads

    @property
    def url(self) -> str:
        return f"tg://user?id={self.telegram_id}"

    @property
    def mention(self) -> str:
        return md.hlink(self.name, self.url)

    def __str__(self) -> str:
        return f"user_id: {self.telegram_id} | user_name: {self.name}"
