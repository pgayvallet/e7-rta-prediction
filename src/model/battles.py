import pydantic
from typing import Optional


class RtaBattleUnit(pydantic.BaseModel):
    id: str
    name: str


class RtaBattle(pydantic.BaseModel):
    schema_version: int

    p1_id: int
    p1_world: str
    p1_grade: str

    p2_id: int
    p2_world: str
    p2_grade: str

    battle_id: int
    season_code: str
    # timestamp
    battle_date: int
    turn_count: int

    p1_win: bool
    p2_win: bool
    p1_first_pick: bool
    p2_first_pick: bool

    prebans: list[RtaBattleUnit]
    p1_prebans: list[RtaBattleUnit]
    p2_prebans: list[RtaBattleUnit]

    # The p1 character that was banned (by p2) and did not play
    p1_postban: Optional[RtaBattleUnit] = None
    # position of the p1 postban (banned by p2), range 1-5
    p1_postban_position: Optional[int] = None
    # The p2 character that was banned (by p1) and did not play
    p2_postban: Optional[RtaBattleUnit] = None
    # position of the p2 postban (banned by p1), range 1-5
    p2_postban_position: Optional[int] = None

    p1_picks: list[RtaBattleUnit]
    p1_pick1: Optional[RtaBattleUnit] = None
    p1_pick2: Optional[RtaBattleUnit] = None
    p1_pick3: Optional[RtaBattleUnit] = None
    p1_pick4: Optional[RtaBattleUnit] = None
    p1_pick5: Optional[RtaBattleUnit] = None

    p2_picks: list[RtaBattleUnit]
    p2_pick1: Optional[RtaBattleUnit] = None
    p2_pick2: Optional[RtaBattleUnit] = None
    p2_pick3: Optional[RtaBattleUnit] = None
    p2_pick4: Optional[RtaBattleUnit] = None
    p2_pick5: Optional[RtaBattleUnit] = None


character_list_mapping = {
    "type": "nested",
    "properties": {
        "id": {"type": "keyword"},
        "name": {"type": "keyword"}
    }
}

character_mapping = {
    "properties": {
        "id": {"type": "keyword"},
        "name": {"type": "keyword"}
    }
}

rta_battle_mappings = {
    "dynamic": "strict",
    "properties": {
        "schema_version": {"type": "integer"},

        # p1 id/rank
        "p1_id": {"type": "long"},
        "p1_world": {"type": "keyword"},
        "p1_grade": {"type": "keyword"},
        # p2 id/rank
        "p2_id": {"type": "long"},
        "p2_world": {"type": "keyword"},
        "p2_grade": {"type": "keyword"},
        # battle id / meta
        "battle_id": {"type": "long"},
        "season_code": {"type": "keyword"},
        "battle_date": {"type": "date"},
        "turn_count": {"type": "integer"},
        # fp / win
        "p1_win": {"type": "boolean"},
        "p2_win": {"type": "boolean"},
        "p1_first_pick": {"type": "boolean"},
        "p2_first_pick": {"type": "boolean"},
        # prebans
        "prebans": character_list_mapping,
        "p1_prebans": character_list_mapping,
        "p2_prebans": character_list_mapping,
        # postban
        "p1_postban": character_mapping,
        "p1_postban_position": {"type": "integer"},
        "p2_postban": character_mapping,
        "p2_postban_position": {"type": "integer"},
        # p1 picks
        "p1_picks": character_mapping,
        "p1_pick1": character_mapping,
        "p1_pick2": character_mapping,
        "p1_pick3": character_mapping,
        "p1_pick4": character_mapping,
        "p1_pick5": character_mapping,
        # p2 picks
        "p2_picks": character_mapping,
        "p2_pick1": character_mapping,
        "p2_pick2": character_mapping,
        "p2_pick3": character_mapping,
        "p2_pick4": character_mapping,
        "p2_pick5": character_mapping,
    }
}
