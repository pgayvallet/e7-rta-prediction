from elasticsearch import AsyncElasticsearch, helpers
from src.model import RtaPlayer, RtaBattle, rta_battle_mappings, rta_player_mappings


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

    async def insert_battles(self, battles: list[RtaBattle], season: str):
        index_name = battle_index(season)

        def bulk_generator():
            for battle in battles:
                yield {
                    "_index": index_name,
                    "_id": battle.battle_id,
                    "_source": battle.model_dump()
                }

        await helpers.async_bulk(self.client, bulk_generator())

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
                    "last_known_rank": player.get("rank", None),
                    "last_update_time": 0,
                    "last_updated_battle_id": 0,
                }

        response = await helpers.async_bulk(self.client, player_generator())
        print(f'insert_player - {response}')

    async def set_player_updated(self, user_id: int, user_world: str, season: str, date: int, last_updated_battle: int):
        index = player_index(season)
        doc_id = f'{user_id}_{user_world}'
        updated_attributes = {
            "last_update_time": date,
            "last_updated_battle_id": last_updated_battle,
        }

        await self.client.update(index=index, id=doc_id, doc=updated_attributes)

    async def get_users_to_refresh(self, num_players: int, season: str):
        response = await self.client.search(
            index=player_index(season),
            size=num_players,
            sort=[
                {"last_update_time": {"order": "asc"}}
            ]
        )
        results = response.body['hits']['hits']
        return list(map(lambda r: RtaPlayer(**r["_source"]), results))
