import asyncio
import aiohttp
import json
import math
from datetime import datetime
import time

from rta_api import api as rta_api
from rta_api.model.get_battle_list import GetBattleListResponseBattleListItem
from src import Indexer, UnitRegistry
from src.model import RtaBattle, RtaPlayer

raw_date_format = "%Y-%m-%d %H:%M:%S.%f"


async def worker(name: str, queue: asyncio.Queue, indexer: Indexer,
                 unit_registry: UnitRegistry, season: str):
    async with aiohttp.ClientSession() as session:
        while True:
            # get the player to process from the queue
            player: RtaPlayer = await queue.get()

            try:
                api_response = await rta_api.get_battle_list(
                    session,
                    user_id=player.user_id,
                    world_code=player.user_world
                )
                battle_list = api_response.result_body.battle_list

                battles = list(map(lambda battle: convert_raw_battle(battle, unit_registry), battle_list))
                max_battle_id = max(list(map(lambda battle: battle.battle_id, battles)))

                # TODO: filter on allowed ranks

                # filter out battles already ingested
                last_updated_battle = player.last_updated_battle_id or 0
                battles = list(filter(lambda battle: battle.battle_id > last_updated_battle, battles))

                # TODO: also update last_known_rank

                # TODO: scan for additional players to add to the queue

                if len(battles) > 0:
                    await indexer.insert_battles(battles, season)

                await indexer.set_player_updated(
                    user_id=player.user_id,
                    user_world=player.user_world,
                    season=season,
                    date=round(time.time() * 1000),
                    last_updated_battle=max_battle_id)

                print(f'updated battles for player {player.user_id} - {len(battles)} battles inserted')
            except Exception as e:
                print(f'error updating user {player.user_id}: {e}')
            finally:
                # Notify the queue that the "work item" has been processed.
                queue.task_done()


async def sync_players_battles(indexer: Indexer,
                               unit_registry: UnitRegistry,
                               season: str,
                               players: list[RtaPlayer],
                               num_worker: int = 3):
    queue = asyncio.Queue()
    for player in players:
        queue.put_nowait(player)

    # Create the worker tasks to process the queue concurrently.
    tasks = []
    for i in range(num_worker):
        task = asyncio.create_task(worker(f'worker-{i}', queue, indexer, unit_registry, season))
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)


def convert_raw_battle(raw: GetBattleListResponseBattleListItem, unit_registry: UnitRegistry) -> 'RtaBattle':

    def unit_from_id(unit_id: str | None):
        if unit_id is None:
            return None
        unit_name = unit_registry.name_from_id(unit_id)
        return {
            "id": unit_id,
            "name": unit_name or "Unknown",
        }

    def units_from_ids(unit_ids: list[str]):
        return list(map(unit_from_id, unit_ids))

    p1_postban = next((char for char in raw.my_deck.hero_list if char.ban == 1), None)
    p2_postban = next((char for char in raw.enemy_deck.hero_list if char.ban == 1), None)
    p1_first_pick = next((char for char in raw.my_deck.hero_list if char.ban == 1), None)

    p1_team_info = json.loads("{" + raw.teamBettleInfo + "}")["my_team"]
    p1_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p1_pick_order = list(map(lambda s: s["hero_code"], p1_team_info))

    p2_team_info = json.loads("{" + raw.teamBettleInfoenemy + "}")["my_team"]
    p2_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p2_pick_order = list(map(lambda s: s["hero_code"], p2_team_info))

    p1_postban_position = p1_pick_order.index(p1_postban.hero_code) + 1 if p1_postban else None
    p2_postban_position = p2_pick_order.index(p2_postban.hero_code) + 1 if p2_postban else None

    battle: dict = {
        "schema_version": 1,

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
    }

    all_prebans = list(set(raw.my_deck.preban_list + raw.enemy_deck.preban_list))
    battle["prebans"] = units_from_ids(all_prebans)

    battle.update({
        "p1_prebans": units_from_ids(raw.my_deck.preban_list),
        "p2_prebans": units_from_ids(raw.enemy_deck.preban_list),

        "p1_postban": unit_from_id(p1_postban.hero_code) if p1_postban is not None else None,
        "p1_postban_position": p1_postban_position,
        "p2_postban": unit_from_id(p2_postban.hero_code) if p2_postban is not None else None,
        "p2_postban_position": p2_postban_position,

        "p1_first_pick": p1_first_pick is not None,
        "p2_first_pick": p1_first_pick is None,

        "p1_picks": units_from_ids(p1_pick_order),
        "p2_picks": units_from_ids(p2_pick_order),
    })

    # p1_pick1 -> p1_pick5
    for n in range(0, 5):
        pick_id = p1_pick_order[n] if len(p1_pick_order) > n else None
        battle[f'p1_pick{n+1}'] = unit_from_id(pick_id)

    # p2_pick1 -> p2_pick5
    for n in range(0, 5):
        pick_id = p2_pick_order[n] if len(p2_pick_order) > n else None
        battle[f'p2_pick{n+1}'] = unit_from_id(pick_id)

    return RtaBattle(**battle)

