from elasticsearch import AsyncElasticsearch


class Indexer:
    client: AsyncElasticsearch

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def create_index(self, index_name: str):
        return await self.client.indices.create(index=index_name, mappings=rta_battle_mappings)


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
