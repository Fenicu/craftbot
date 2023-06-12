from odmantic import Model

try:
    import ujson as json
except ImportError:
    import json


class CollectionType(Model):
    """
    Модель сета
    """

    name: str
    icon: str

    class Config:
        collection = "sets"
        json_loads = json.loads

    def __str__(self) -> str:
        return f"set_id: {self.id} | set_name: {self.name} {self.icon}"
