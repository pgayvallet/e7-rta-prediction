import asyncio
import aiohttp
import json
import math
from datetime import datetime
import time

from rta_api import api as rta_api
from rta_api.model.get_battle_list import GetBattleListResponseBattleListItem
from src import Indexer
from src.model import RtaBattle, RtaPlayer

raw_date_format = "%Y-%m-%d %H:%M:%S.%f"


async def worker(name: str, queue: asyncio.Queue, indexer: Indexer, season: str):
    async with aiohttp.ClientSession() as session:
        while True:
            # Get a "work item" out of the queue.
            player: RtaPlayer = await queue.get()

            try:
                response = await rta_api.get_battle_list(
                    session,
                    user_id=player.user_id,
                    world_code=player.user_world
                )
                battle_list = response.result_body.battle_list

                battles = list(map(convert_raw_battle, battle_list))

                # TODO: check error, e.g 79084216 or 104467101 - max() arg is an empty sequence

                # TODO: filter on allowed ranks
                # TODO: fetch user to check last_updated_battle_id and filter
                # TODO: also update last_known_rank

                max_battle_id = max(list(map(lambda battle: battle['battle_id'], battles)))

                await indexer.insert_battles(battles, season)
                await indexer.set_player_updated(
                    user_id=player.user_id,
                    user_world=player.user_world,
                    season=season,
                    date=round(time.time() * 1000),
                    last_updated_battle=max_battle_id)

                print(f'fetched battles for player {player.user_id} - {len(battle_list)} battles')
            except Exception as e:
                print(f'error updating user {player.user_id}: {e}')
            finally:
                # Notify the queue that the "work item" has been processed.
                queue.task_done()


async def sync_players_battles(indexer: Indexer,
                               season: str,
                               players: list[RtaPlayer],
                               num_worker: int = 3):
    queue = asyncio.Queue()
    for player in players:
        queue.put_nowait(player)

    # Create the worker tasks to process the queue concurrently.
    tasks = []
    for i in range(num_worker):
        task = asyncio.create_task(worker(f'worker-{i}', queue, indexer, season))
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)


def convert_raw_battle(raw: GetBattleListResponseBattleListItem) -> 'RtaBattle':
    p1_postban = next(char for char in raw.my_deck.hero_list if char.ban == 1)
    p2_postban = next(char for char in raw.enemy_deck.hero_list if char.ban == 1)
    p1_first_pick = next((char for char in raw.my_deck.hero_list if char.ban == 1), None)

    p1_team_info = json.loads("{" + raw.teamBettleInfo + "}")["my_team"]
    p1_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p1_pick_order = list(map(lambda s: s["hero_code"], p1_team_info))

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

        "battle_id": int(raw.battle_seq),
        "season_code": raw.season_code,
        "turn_count": raw.turn,
        "battle_date": math.floor(datetime.strptime(raw.battle_day, raw_date_format).timestamp() * 1000),

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
        "p1_pick1": p1_pick_order[0] if len(p1_pick_order) > 0 else None,
        "p1_pick2": p1_pick_order[1] if len(p1_pick_order) > 1 else None,
        "p1_pick3": p1_pick_order[2] if len(p1_pick_order) > 2 else None,
        "p1_pick4": p1_pick_order[3] if len(p1_pick_order) > 3 else None,
        "p1_pick5": p1_pick_order[4] if len(p1_pick_order) > 4 else None,

        "p2_picks": p2_pick_order,
        "p2_pick1": p2_pick_order[0] if len(p2_pick_order) > 0 else None,
        "p2_pick2": p2_pick_order[1] if len(p2_pick_order) > 1 else None,
        "p2_pick3": p2_pick_order[2] if len(p2_pick_order) > 2 else None,
        "p2_pick4": p2_pick_order[3] if len(p2_pick_order) > 3 else None,
        "p2_pick5": p2_pick_order[4] if len(p2_pick_order) > 4 else None,
    }
    return battle
