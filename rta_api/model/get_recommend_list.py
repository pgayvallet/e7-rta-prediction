import pydantic


class GetRecommendListResponseList(pydantic.BaseModel):
    regDate: str
    seasonCode: str
    hero_code: str
    nickname: str
    world_code: str
    nick_no: int
    rank: int


class GetRecommendListRecommendedList(pydantic.BaseModel):
    recommend_list: list[GetRecommendListResponseList]
    # return_code: int
