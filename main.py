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

    ## Khhm
    ## await commands.sync_player_battles(192119856, "world_eu")

    current_season = 'pvp_rta_ss12'

    client = create_client()
    indexer = Indexer(client=client)

    await indexer.create_player_index(season=current_season)
    await indexer.create_battle_index(season=current_season)
    # await indexer.insert_players([
    #    {"id": 192119856, "world": "world_eu"},
    #    {"id": 71212252, "world": "world_asia"}
    # ], 'pvp_rta_ss12')

    players = await indexer.get_users_to_refresh(10, current_season)

    await commands.sync_players_battles(indexer, players, num_worker=3)

    print(players)
    await client.close()

    return

    players = await commands.fetch_player_list(
        destination_file="./data/users.json",
        num_worker=3,
        max_users=800,
        initial_recommend_count=5)

    def map_player(player):
        return {
            "id": player["user_id"],
            "name": player["user_name"],
            "world": player["world_code"],
            "rank": player["user_rank"],
        }

    await indexer.insert_players(
        list(map(map_player, players.values())),
        'pvp_rta_ss12'
    )

    await client.close()

    ## await commands.sync_hero_list()



    try:
        # response = await indexer.create_index("foo_1")
        # print(response.body)

        documents = await commands.sync_player_battles(192119856, "world_eu")
        print(documents)
        for document in documents:
            await client.index(
                index="foo_1",
                id=document["battle_id"],
                document=document)
    except Exception as e:
        print(e)
    finally:
        await client.close()


asyncio.run(main())
