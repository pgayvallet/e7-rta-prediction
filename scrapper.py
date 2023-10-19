import asyncio
import aiohttp
from typing import TypedDict
import time
import rta_api


class UserInfo(TypedDict):
    user_id: int
    world_code: str


async def worker(name, queue, userDict):
    async with aiohttp.ClientSession() as session:
        while True:
            # Get a "work item" out of the queue.
            task = await queue.get()

            print(f'{name} - received task {task}')

            match task["action"]:
                case "fetch_recommend_list":
                    response = await rta_api.get_recommended_list(session)
                    for player in response.recommend_list:
                        player_id_str = f'{player.nick_no}-{player.world_code}'
                        if userDict.get(player_id_str) is None:
                            print(f'{name} - adding player {player.nick_no} - {player.world_code}')
                            await queue.put({
                                "action": "fetch_battle_list",
                                "user_id": player.nick_no,
                                "world_code": player.world_code
                            })
                            # TODO: properly add to userDict
                            userDict[player_id_str] = "FILLED"
                        else:
                            print(f'{name} - player {player.nick_no} - {player.world_code} - already processed')


                case "fetch_battle_list":
                    response = await rta_api.get_battle_list(session, user_id=task["user_id"], world_code=task["world_code"])
                    for battle in response.result_body.battle_list:
                        player_id_str = f'{battle.matchPlayerNicknameno}-{battle.enemy_world_code}'
                        if userDict.get(player_id_str) is None:
                            print(f'{name} - adding player {battle.matchPlayerNicknameno} - {battle.enemy_world_code}')
                            await queue.put({
                                "action": "fetch_battle_list",
                                "user_id": battle.matchPlayerNicknameno,
                                "world_code": battle.enemy_world_code,
                            })
                            # TODO: properly add to userDict
                            userDict[player_id_str] = "FILLED"
                        else:
                            print(f'{name} - player {battle.matchPlayerNicknameno} - {battle.enemy_world_code} - already processed')

            print(f'{name} - task done')

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


async def main():
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()

    userDict: dict[str, UserInfo] = {}
    userDict["foo"] = UserInfo(user_id=12, world_code="fr")

    # start by fetching the recommended list 3 times (results will differ)
    for _ in range(3):
        queue.put_nowait({
            "action": "fetch_recommend_list"
        })

    # Create the worker tasks to process the queue concurrently.
    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', queue, userDict))
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    # for task in tasks:
    #     task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    print('====')


asyncio.run(main())
