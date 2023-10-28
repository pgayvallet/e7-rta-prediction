import asyncio
import aiohttp
import json
from typing import TypedDict
from rta_api import api as rta_api
from src import Indexer
from src.constants import ALLOWED_PLAYER_RANKS, RANK_LEGEND
from src.utils import get_user_uuid


class UserInfo(TypedDict):
    user_id: int
    user_name: str
    world_code: str
    user_rank: str


async def worker(name: str,
                 queue: asyncio.Queue,
                 season: str,
                 user_dict: dict[str, UserInfo],
                 max_count: int):
    async def enqueue_user_if_needed(
            user_id: int,
            user_name: str,
            world_code: str,
            current_rank: str,
            match_season: str,
    ):
        player_uuid = get_user_uuid(user_id, world_code)
        if current_rank not in ALLOWED_PLAYER_RANKS or match_season != season:
            return
        if user_dict.get(player_uuid) is None:
            # print(f'{name} - adding player {player.nick_no} - {player.world_code}')
            await queue.put({
                "action": "fetch_battle_list",
                "user_id": user_id,
                "world_code": world_code
            })
            user_dict[player_uuid] = {
                "user_id": user_id,
                "user_name": user_name,
                "world_code": world_code,
                "user_rank": current_rank,
            }

    async with aiohttp.ClientSession() as session:
        while True:
            # Get a "work item" out of the queue.
            task = await queue.get()

            # exit earlier if we've reached our goal
            if len(user_dict) > max_count:
                queue.task_done()
                continue

            # print(f'{name} - received task {task}')

            match task["action"]:
                case "fetch_recommend_list":
                    response = await rta_api.get_recommended_list(session)
                    for player in response.recommend_list:
                        await enqueue_user_if_needed(user_id=player.nick_no,
                                                     user_name=player.nickname,
                                                     world_code=player.world_code,
                                                     current_rank=RANK_LEGEND,
                                                     match_season=season)
                case "fetch_battle_list":
                    response = await rta_api.get_battle_list(session,
                                                             user_id=task["user_id"],
                                                             world_code=task["world_code"])
                    for battle in response.result_body.battle_list:
                        await enqueue_user_if_needed(user_id=battle.matchPlayerNicknameno,
                                                     user_name=battle.enemy_nick_no,
                                                     world_code=battle.enemy_world_code,
                                                     current_rank=battle.enemy_grade_code,
                                                     match_season=battle.season_code)

            print(f'{name} - task done - total user added: {len(user_dict)}, elements in queue: {queue.qsize()}')

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


async def fetch_player_list(indexer: Indexer,
                            season: str,
                            num_worker: int = 3,
                            initial_recommend_count: int = 5,
                            max_users: int = 500):
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()

    user_dict: dict[str, UserInfo] = {}

    # start by fetching the recommended list 3 times (results will differ)
    for _ in range(initial_recommend_count):
        queue.put_nowait({
            "action": "fetch_recommend_list"
        })

    # Create the worker tasks to process the queue concurrently.
    tasks = []
    for i in range(num_worker):
        task = asyncio.create_task(worker(f'worker-{i}', queue, season, user_dict, max_count=max_users))
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    def map_player(player):
        return {
            "id": player["user_id"],
            "name": player["user_name"],
            "world": player["world_code"],
            "rank": player["user_rank"],
        }

    await indexer.insert_players(
        list(map(map_player, user_dict.values())),
        season
    )

    print(f'inserted {len(user_dict)} users')
