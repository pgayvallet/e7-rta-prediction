import pydantic


class GetBattleListResponseBattleListItemDeckHero(pydantic.BaseModel):
    hero_code: str
    first_pick: int
    mvp: int
    ban: int


class GetBattleListResponseBattleListItemDeck(pydantic.BaseModel):
    preban_list: list[str]
    hero_list: list[GetBattleListResponseBattleListItemDeckHero]


class GetBattleListResponseBattleListItem(pydantic.BaseModel):
    # player id of the active player
    nicknameno: int
    worldCode: str
    # player id of the opponent
    matchPlayerNicknameno: int
    # game id
    battle_seq: str
    # id of the season
    season_code: str
    # grade code of the player
    grade_code: str
    # grade code of the player
    enemy_grade_code: str
    # e.g world_jpn
    enemy_world_code: str
    # the nickname (*not* id) of the opponent
    enemy_nick_no: str
    # 1 - win | 0 - loose
    iswin: int
    # timestamp, "2023-10-18 14:55:39.0" format
    battle_day: str
    # active player deck
    my_deck: GetBattleListResponseBattleListItemDeck
    # opponent deck
    enemy_deck: GetBattleListResponseBattleListItemDeck

    # we gonna need to check that later
    teamBettleInfoenemy: str
    teamBettleInfo: str


class GetBattleListResponseResultBody(pydantic.BaseModel):
    nick_no: int
    world_code: str
    battle_list: list[GetBattleListResponseBattleListItem]


class GetBattleListResponse(pydantic.BaseModel):
    """
    The top level response for the GetBattleList api
    """
    result_body: GetBattleListResponseResultBody
    return_code: int
