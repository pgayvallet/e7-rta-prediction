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
        for raw_battle in battle_list[0:3]:
            battle = convert_raw_battle(raw_battle)
            print(battle)


class RtaBattle(TypedDict):
    p1_id: int
    p1_world: str
    # p1_nick: str
    p1_grade: str

    p2_id: int
    p2_world: str
    # p2_nick: str
    p2_grade: str

    ## TODO: seems an integer, safe to convert?
    battle_id: str
    season_code: str

    p1_win: bool
    p2_win: bool


def convert_raw_battle(raw: GetBattleListResponseBattleListItem) -> 'RtaBattle':
    battle: RtaBattle = {
        "p1_id": raw.nicknameno,
        "p1_world": raw.worldCode,
        "p1_grade": raw.grade_code,

        "p2_id": raw.matchPlayerNicknameno,
        "p2_world": raw.enemy_world_code,
        "p2_grade": raw.enemy_grade_code,

        "battle_id": raw.battle_seq,
        "season_code": raw.season_code,

        "p1_win": raw.iswin == 1,
        "p2_win": raw.iswin == 2,
    }
    return battle
