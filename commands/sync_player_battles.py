import asyncio
import aiohttp
import json
import math
from datetime import datetime
import time
from typing import TypedDict
import pydantic

from rta_api import api as rta_api
from rta_api.model.get_battle_list import GetBattleListResponseBattleListItem
from src import Indexer, UnitRegistry, ArtefactRegistry
from src.model import RtaBattle, RtaPlayer
from src.constants import ALLOWED_PLAYER_RANKS
from src.utils import get_user_uuid

raw_date_format = "%Y-%m-%d %H:%M:%S.%f"


# TODO: factorize with fetch_player_list
class UserInfo(TypedDict):
    id: int
    name: str
    world: str
    rank: str


async def worker(
        name: str,
        queue: asyncio.Queue,
        indexer: Indexer,
        unit_registry: UnitRegistry,
        artefact_registry: ArtefactRegistry,
        season: str,
        known_player_uuids: set[str],
        sync_discovered_players: bool,
):
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

                battles = list(
                    map(lambda battle: convert_raw_battle(battle, unit_registry, artefact_registry), battle_list))
                max_battle_id = max(list(map(lambda battle: battle.battle_id, battles)))

                # filter out battles already ingested
                last_updated_battle = player.last_updated_battle_id or 0

                def filter_battles(battle: RtaBattle) -> 'bool':
                    # already processed - skipping
                    if battle.battle_id <= last_updated_battle:
                        return False
                    # not in correct season - skipping
                    if battle.season_code != season:
                        return False
                    # only import if at least one player is in the allowed ranks
                    if battle.p1_grade not in ALLOWED_PLAYER_RANKS and battle.p2_grade not in ALLOWED_PLAYER_RANKS:
                        return False
                    return True

                battles = list(filter(filter_battles, battles))

                discovered_players = []
                for raw_battle in battle_list:
                    opponent_uuid = get_user_uuid(raw_battle.matchPlayerNicknameno, raw_battle.enemy_world_code)
                    opponent_rank = raw_battle.enemy_grade_code
                    if (
                            opponent_uuid not in known_player_uuids
                            and opponent_rank in ALLOWED_PLAYER_RANKS
                            and raw_battle.season_code == season
                    ):
                        known_player_uuids.add(opponent_uuid)
                        discovered_players.append({
                            "id": raw_battle.matchPlayerNicknameno,
                            "name": raw_battle.enemy_nick_no,
                            "world": raw_battle.enemy_world_code,
                            "rank": raw_battle.enemy_grade_code,
                        })

                if len(discovered_players) > 0:
                    await indexer.insert_players(discovered_players, season)

                    if sync_discovered_players:
                        for discovered_player in discovered_players:
                            await queue.put(RtaPlayer(**{
                                "user_id": discovered_player['id'],
                                "user_world": discovered_player['world'],
                                "user_name": discovered_player['name'],
                                "last_known_rank": discovered_player['rank'],
                            }))

                if len(battles) > 0:
                    await indexer.insert_battles(battles, season)

                # TODO: this is wrong, can be p1 or p2... need to check
                last_known_rank = battles[0].p1_grade if len(battles) > 0 else player.last_known_rank

                await indexer.set_player_updated(
                    user_id=player.user_id,
                    user_world=player.user_world,
                    season=season,
                    date=round(time.time() * 1000),
                    last_updated_battle=max_battle_id,
                    last_known_rank=last_known_rank)

                print(f'updated battles for player {player.user_id} - {len(battles)} battles inserted - {len(discovered_players)} players discovered')
                print(f'remaining items in queue: {queue.qsize()}')
            except Exception as e:
                print(f'error updating user {player.user_id}: {e}')
            finally:
                # Notify the queue that the "work item" has been processed.
                queue.task_done()


async def sync_players_battles(
        indexer: Indexer,
        unit_registry: UnitRegistry,
        artefact_registry: ArtefactRegistry,
        players_to_sync: list[RtaPlayer],
        known_player_uuids: set[str],
        season: str,
        sync_discovered_players: bool,
        num_worker: int = 3
):
    queue: asyncio.Queue = asyncio.Queue()
    for player in players_to_sync:
        queue.put_nowait(player)

    # Create the worker tasks to process the queue concurrently.
    tasks = []
    for i in range(num_worker):
        task = asyncio.create_task(
            worker(
                f'worker-{i}',
                queue,
                indexer,
                unit_registry,
                artefact_registry,
                season,
                known_player_uuids,
                sync_discovered_players
            )
        )
        tasks.append(task)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)


def convert_raw_battle(raw: GetBattleListResponseBattleListItem,
                       unit_registry: UnitRegistry,
                       artefact_registry: ArtefactRegistry) -> 'RtaBattle':
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

    p1_first_pick = next((char for char in raw.my_deck.hero_list if char.first_pick == 1), None)

    p1_team_battle_info = json.loads("{" + raw.teamBettleInfo + "}")
    p1_team_info = p1_team_battle_info["my_team"]
    p1_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p1_pick_order = list(map(lambda s: s["hero_code"], p1_team_info))

    p2_team_battle_info = json.loads("{" + raw.teamBettleInfoenemy + "}")
    p2_team_info = p2_team_battle_info["my_team"]
    p2_team_info.sort(key=lambda x: x["pick_order"], reverse=False)
    p2_pick_order = list(map(lambda s: s["hero_code"], p2_team_info))

    p1_postban_position = p1_pick_order.index(p1_postban.hero_code) + 1 if p1_postban else None
    p2_postban_position = p2_pick_order.index(p2_postban.hero_code) + 1 if p2_postban else None

    battle_date = math.floor(datetime.strptime(raw.battle_day, raw_date_format).timestamp() * 1000)

    battle: dict = {
        "schema_version": 1,

        "battle_id": int(raw.battle_seq),
        "season_code": raw.season_code,
        "turn_count": raw.turn,
        "battle_date": battle_date,
    }

    reverse_players = p1_first_pick is None
    p1_prefix = 'p2' if reverse_players else 'p1'
    p2_prefix = 'p1' if reverse_players else 'p2'

    battle.update({
        f'{p1_prefix}_id': raw.nicknameno,
        f'{p1_prefix}_world': raw.worldCode,
        f'{p1_prefix}_grade': raw.grade_code,
        f'{p1_prefix}_win': raw.iswin == 1,
        f'{p1_prefix}_first_pick': p1_first_pick is not None,

        f'{p2_prefix}_id': raw.matchPlayerNicknameno,
        f'{p2_prefix}_world': raw.enemy_world_code,
        f'{p2_prefix}_grade': raw.enemy_grade_code,
        f'{p2_prefix}_win': raw.iswin == 2,
        f'{p2_prefix}_first_pick': p1_first_pick is None,
    })

    all_prebans = list(set(raw.my_deck.preban_list + raw.enemy_deck.preban_list))
    battle["prebans"] = units_from_ids(all_prebans)

    battle.update({
        f'{p1_prefix}_prebans': units_from_ids(raw.my_deck.preban_list),
        f'{p1_prefix}_postban': unit_from_id(p1_postban.hero_code) if p1_postban is not None else None,
        f'{p1_prefix}_postban_position': p1_postban_position,

        f'{p2_prefix}_prebans': units_from_ids(raw.enemy_deck.preban_list),
        f'{p2_prefix}_postban': unit_from_id(p2_postban.hero_code) if p2_postban is not None else None,
        f'{p2_prefix}_postban_position': p2_postban_position,
    })

    battle[f'{p1_prefix}_picks'] = units_from_ids(p1_pick_order)
    battle[f'{p2_prefix}_picks'] = units_from_ids(p2_pick_order)

    # p1_pick1 -> p1_pick5
    for n in range(0, 5):
        pick_id = p1_pick_order[n] if len(p1_pick_order) > n else None
        battle[f'{p1_prefix}_pick{n + 1}'] = unit_from_id(pick_id)

    # p2_pick1 -> p2_pick5
    for n in range(0, 5):
        pick_id = p2_pick_order[n] if len(p2_pick_order) > n else None
        battle[f'{p2_prefix}_pick{n + 1}'] = unit_from_id(pick_id)

    p1_picks = units_from_ids(p2_pick_order if reverse_players else p1_pick_order)
    p2_picks = units_from_ids(p1_pick_order if reverse_players else p2_pick_order)

    battle["p1_picks_stage1"] = p1_picks[0:1]
    battle["p1_picks_stage2"] = p1_picks[1:3]
    battle["p1_picks_stage3"] = p1_picks[3:5]

    battle["p2_picks_stage1"] = p2_picks[0:2]
    battle["p2_picks_stage2"] = p2_picks[2:4]
    battle["p2_picks_stage3"] = p2_picks[4:5]

    parsed_p1_team_info = TeamBattleInfo(**p1_team_battle_info)
    parsed_p2_team_info = TeamBattleInfo(**p2_team_battle_info)
    all_unit_details = parsed_p1_team_info.my_team + parsed_p2_team_info.my_team

    def map_unit_details(raw: TeamBattleInfoDetails):
        return {
            "id": raw.hero_code,
            "name": unit_registry.name_from_id(raw.hero_code),
            "pick_order": raw.pick_order,
            "equipped_sets": raw.equip,
            "artifact_id": raw.artifact,
            "artifact_name": artefact_registry.name_from_id(raw.artifact) or "Unknown",
            "mvp": raw.mvp == 1,
            "position": raw.position,
            "role": raw.job_cd,
        }

    battle["units_details"] = list(map(map_unit_details, all_unit_details))

    initial_cr_position = json.loads("{" + raw.energyGauge + "}")["energy_gauge"]
    battle["initial_cr_position"] = initial_cr_position

    return RtaBattle(**battle)


class TeamBattleInfoDetails(pydantic.BaseModel):
    pick_order: int
    hero_code: str
    artifact: str
    equip: list[str]
    mvp: int  # 0 / 1
    kill_count: int
    position: int
    attack_damage: float
    receive_damage: float
    job_cd: str


class TeamBattleInfo(pydantic.BaseModel):
    my_team: list[TeamBattleInfoDetails]
