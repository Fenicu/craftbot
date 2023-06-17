from odmantic import Model

try:
    import ujson as json
except ImportError:
    import json


class GroupType(Model):
    """
    Модель группы пользователей
    """

    owner: int
    name: str

    class Config:
        collection = "groups"
        json_loads = json.loads

    @property
    def join_command(self) -> str:
        return f"/join {self.id}"

    def __str__(self) -> str:
        return f"owner_id: {self.owner} | name: {self.name}"
