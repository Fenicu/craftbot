from bson import ObjectId
from odmantic import Model

try:
    import ujson as json
except ImportError:
    import json


class UserInGroupType(Model):
    """
    Модель пользователя в группе
    """

    group: ObjectId
    user: int

    class Config:
        collection = "UsersInGroups"
        json_loads = json.loads

    def __str__(self) -> str:
        return f"group: {self.group} | user: {self.user}"
