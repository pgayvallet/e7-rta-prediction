from elasticsearch import AsyncElasticsearch, helpers
import pydantic
from typing import Optional


class RtaPlayer(pydantic.BaseModel):
    user_id: int
    user_world: str
    user_name: str
    last_known_rank: str
    last_fetch_time: Optional[int] = None


def player_index(season: str):
    return f'rta_players_{season}'

def battle_index(season: str):
    return f'rta_battles_{season}'

class Indexer:
    client: AsyncElasticsearch

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    # BATTLE APIS

    async def create_battle_index(self, season: str):
        index_name = battle_index(season)
        exists_check = await self.client.indices.exists(index=index_name)
        exists = exists_check.meta.status == 200
        if not exists:
            await self.client.indices.create(index=index_name, mappings=rta_battle_mappings)


    # PLAYER APIS

    async def create_player_index(self, season: str):
        index_name = player_index(season)
        exists_check = await self.client.indices.exists(index=index_name)
        exists = exists_check.meta.status == 200
        if not exists:
            await self.client.indices.create(index=index_name, mappings=rta_player_mappings)

    async def insert_players(self, players: list[dict], season: str):
        index = player_index(season)

        def player_generator():
            for player in players:
                yield {
                    "_index": index,
                    "_id": f'{player["id"]}_{player["world"]}',
                    "user_id": player["id"],
                    "user_name": player["name"],
                    "user_world": player["world"],
                    "last_known_rank": player.get("rank", None)
                }

        response = await helpers.async_bulk(self.client, player_generator())
        print(f'insert_player - {response}')

    async def get_users_to_refresh(self, num_players: int, season: str):
        response = await self.client.search(
            index=player_index(season),
            size=num_players,
            sort=[
                {"last_fetch_time": {"order": "asc"}}
            ]
        )
        results = response.body['hits']['hits']
        return list(map(lambda r: RtaPlayer(**r["_source"]), results))


rta_battle_mappings = {
    "dynamic": "strict",
    "properties": {
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
        "prebans": {"type": "keyword"},
        "p1_prebans": {"type": "keyword"},
        "p2_prebans": {"type": "keyword"},
        # postban
        "p1_postban": {"type": "keyword"},
        "p1_postban_position": {"type": "integer"},
        "p2_postban": {"type": "keyword"},
        "p2_postban_position": {"type": "integer"},
        # p1 picks
        "p1_picks": {"type": "keyword"},
        "p1_pick1": {"type": "keyword"},
        "p1_pick2": {"type": "keyword"},
        "p1_pick3": {"type": "keyword"},
        "p1_pick4": {"type": "keyword"},
        "p1_pick5": {"type": "keyword"},
        # p2 picks
        "p2_picks": {"type": "keyword"},
        "p2_pick1": {"type": "keyword"},
        "p2_pick2": {"type": "keyword"},
        "p2_pick3": {"type": "keyword"},
        "p2_pick4": {"type": "keyword"},
        "p2_pick5": {"type": "keyword"},
    }
}

rta_player_mappings = {
    "dynamic": "strict",
    "properties": {
        "user_id": {"type": "long"},
        "user_world": {"type": "keyword"},
        "user_name": {"type": "keyword"},
        "last_known_rank": {"type": "keyword"},
        "last_fetch_time": {"type": "date"},
    }
}
