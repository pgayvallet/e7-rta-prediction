from typing import TypedDict


class RtaBattle(TypedDict):
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

    prebans: list[str]
    p1_prebans: list[str]
    p2_prebans: list[str]

    # The p1 character that was banned (by p2) and did not play
    p1_postban: str
    # The p2 character that was banned (by p1) and did not play
    p2_postban: str

    p1_picks: list[str]
    p1_pick1: str
    p1_pick2: str
    p1_pick3: str
    p1_pick4: str
    p1_pick5: str

    p2_picks: list[str]
    p2_pick1: str
    p2_pick2: str
    p2_pick3: str
    p2_pick4: str
    p2_pick5: str

    # position of the p1 postban (banned by p2), range 1-5
    p1_postban_position: int
    # position of the p2 postban (banned by p1), range 1-5
    p2_postban_position: int
