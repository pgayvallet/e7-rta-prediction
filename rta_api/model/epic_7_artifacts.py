import pydantic


class ArtefactListArtefact(pydantic.BaseModel):
    code: str
    name: str


class ArtefactList(pydantic.BaseModel):
    en: list[ArtefactListArtefact]
