import pydantic
import json


class Artefact(pydantic.BaseModel):
    id: str
    name: str


class ArtefactRegistry:
    registry: dict[str, Artefact] = {}

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
                self.registry[key] = Artefact(**value)
