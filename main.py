import asyncio
import commands
from src import create_client, Indexer


async def main():
    """
    await commands.fetch_player_list(
        destination_file="./data/users.json",
        num_worker=3,
        max_users=2000,
        initial_recommend_count=5)
    """

    current_season = 'pvp_rta_ss12'
    client = create_client()
    indexer = Indexer(client=client)

    await indexer.create_player_index(season=current_season)
    await indexer.create_battle_index(season=current_season)

    players = await indexer.get_users_to_refresh(1, current_season)
    await commands.sync_players_battles(indexer, current_season, players, num_worker=3)
    await client.close()
    return

    # players = await commands.fetch_player_list(
    #     destination_file="./data/users.json",
    #     num_worker=3,
    #     max_users=850,
    #     initial_recommend_count=5)
    # 
    # def map_player(player):
    #     return {
    #         "id": player["user_id"],
    #         "name": player["user_name"],
    #         "world": player["world_code"],
    #         "rank": player["user_rank"],
    #     }
    # 
    # await indexer.insert_players(
    #     list(map(map_player, players.values())),
    #     current_season
    # )

    await client.close()

    return



    # try:
    #     # response = await indexer.create_index("foo_1")
    #     # print(response.body)
    #
    #     documents = await commands.sync_player_battles(192119856, "world_eu")
    #     print(documents)
    #     for document in documents:
    #         await client.index(
    #             index="foo_1",
    #             id=document["battle_id"],
    #             document=document)
    # except Exception as e:
    #     print(e)
    # finally:
    #     await client.close()


asyncio.run(main())
