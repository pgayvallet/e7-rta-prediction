import asyncio
import aiohttp
import json
from typing import TypedDict
from rta_api import api as rta_api
from rta_api.model.get_battle_list import GetBattleListResponseBattleListItem


async def worker(name: str, queue: asyncio.Queue):
    async with aiohttp.ClientSession() as session:
        while True:
            # Get a "work item" out of the queue.
            task = await queue.get()

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


async def sync_player_battles(user_id: int,
                              world_code: str):
    # Create a queue that we will use to store our "workload".
    # queue = asyncio.Queue()
    async with aiohttp.ClientSession() as session:
        response = await rta_api.get_battle_list(session, user_id=user_id, world_code=world_code)
        battle_list = response.result_body.battle_list
        for raw_battle in battle_list[0:1]:
            battle = convert_raw_battle(raw_battle)
            print(json.dumps(battle, indent=2))


class RtaBattle(TypedDict):
    p1_id: int
    p1_world: str
    p1_grade: str

    p2_id: int
    p2_world: str
    p2_grade: str

    ## TODO: seems an integer, safe to convert?
    battle_id: str
    season_code: str

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

    ## TODO: "2023-10-18 14:55:39.0"
    battle_date: int # timestamp


def convert_raw_battle(raw: GetBattleListResponseBattleListItem) -> 'RtaBattle':
    p1_postban = next(char for char in raw.my_deck.hero_list if char.ban == 1)
    p2_postban = next(char for char in raw.enemy_deck.hero_list if char.ban == 1)
    p1_first_pick = next((char for char in raw.my_deck.hero_list if char.ban == 1), None)

    ###
    p1_team_info = json.loads("{" + raw.teamBettleInfo + "}")["my_team"]
    p1_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p1_pick_order = list(map(lambda s: s["hero_code"], p1_team_info))
    ###

    p2_team_info = json.loads("{" + raw.teamBettleInfoenemy + "}")["my_team"]
    p2_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p2_pick_order = list(map(lambda s: s["hero_code"], p2_team_info))

    p1_postban_position = p1_pick_order.index(p1_postban.hero_code) + 1
    p2_postban_position = p2_pick_order.index(p2_postban.hero_code) + 1

    battle: RtaBattle = {
        "p1_id": raw.nicknameno,
        "p1_world": raw.worldCode,
        "p1_grade": raw.grade_code,

        "p2_id": raw.matchPlayerNicknameno,
        "p2_world": raw.enemy_world_code,
        "p2_grade": raw.enemy_grade_code,

        "battle_id": raw.battle_seq,
        "season_code": raw.season_code,
        "turn_count": raw.turn,

        "p1_win": raw.iswin == 1,
        "p2_win": raw.iswin == 2,

        "prebans": list(set(raw.my_deck.preban_list + raw.enemy_deck.preban_list)),
        "p1_prebans": raw.my_deck.preban_list,
        "p2_prebans": raw.enemy_deck.preban_list,

        "p1_postban": p1_postban.hero_code,
        "p1_postban_position": p1_postban_position,
        "p2_postban": p2_postban.hero_code,
        "p2_postban_position": p2_postban_position,

        "p1_first_pick": p1_first_pick is not None,
        "p2_first_pick": p1_first_pick is None,

        "p1_picks": p1_pick_order,
        "p1_pick1": p1_pick_order[0],
        "p1_pick2": p1_pick_order[1],
        "p1_pick3": p1_pick_order[2],
        "p1_pick4": p1_pick_order[3],
        "p1_pick5": p1_pick_order[4],

        "p2_picks": p2_pick_order,
        "p2_pick1": p2_pick_order[0],
        "p2_pick2": p2_pick_order[1],
        "p2_pick3": p2_pick_order[2],
        "p2_pick4": p2_pick_order[3],
        "p2_pick5": p2_pick_order[4],
    }
    return battle
