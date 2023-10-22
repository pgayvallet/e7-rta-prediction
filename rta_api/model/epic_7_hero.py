import pydantic


class HeroListHero(pydantic.BaseModel):
    code: str
    grade: str
    name: str
    job_cd: str
    attribute_cd: str


class HeroList(pydantic.BaseModel):
    en: list[HeroListHero]
