import asyncio
import aiohttp
import json
from typing import TypedDict
from rta_api import api as rta_api
from src.constants import ALLOWED_PLAYER_RANKS, RANK_LEGEND


class UserInfo(TypedDict):
    user_id: int
    user_name: str
    world_code: str
    user_rank: str


allowed_ranks_set = set(ALLOWED_PLAYER_RANKS)


async def worker(name: str,
                 queue: asyncio.Queue,
                 user_dict: dict[str, UserInfo],
                 max_count: int):

    async def enqueue_user_if_needed(user_id: int, user_name: str, world_code: str, current_rank: str):
        player_id_str = f'{user_id}-{world_code}'
        if current_rank not in allowed_ranks_set:
            return
        if user_dict.get(player_id_str) is None:
            # print(f'{name} - adding player {player.nick_no} - {player.world_code}')
            await queue.put({
                "action": "fetch_battle_list",
                "user_id": user_id,
                "world_code": world_code
            })
            user_dict[player_id_str] = {
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
                                                     current_rank=RANK_LEGEND)
                case "fetch_battle_list":
                    response = await rta_api.get_battle_list(session,
                                                             user_id=task["user_id"],
                                                             world_code=task["world_code"])
                    for battle in response.result_body.battle_list:
                        await enqueue_user_if_needed(user_id=battle.matchPlayerNicknameno,
                                                     user_name=battle.enemy_nick_no,
                                                     world_code=battle.enemy_world_code,
                                                     current_rank=battle.enemy_grade_code)

            print(f'{name} - task done - total user added: {len(user_dict)}, elements in queue: {queue.qsize()}')

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


async def fetch_player_list(destination_file: str,
                            num_worker: int = 3,
                            initial_recommend_count: int = 5,
                            max_users: int = 2000) -> 'dict[str, UserInfo]':
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
        task = asyncio.create_task(worker(f'worker-{i}', queue, user_dict, max_count=max_users))
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    print(f'fetched {len(user_dict)} users')

    user_file = open(destination_file, "w")
    user_file.write(json.dumps(list(user_dict.values()), indent=2, ensure_ascii=False))
    user_file.close()

    return user_dict
