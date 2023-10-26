import pydantic
import json


class Unit(pydantic.BaseModel):
    id: str
    name: str
    grade: str
    role: str
    element: str


class UnitRegistry:
    registry: dict[str, Unit] = {}

    def __init__(self, filepath: str):
        self.__load(filepath)

    def name_from_id(self, unit_id: str):
        if unit_id in self.registry:
            return self.registry[unit_id].name
        return None

    def __load(self, filepath: str):
        with open(filepath, "r") as unit_file:
            data: dict = json.load(unit_file)
            for key, value in data.items():
                self.registry[key] = Unit(**value)
