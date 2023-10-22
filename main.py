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

    client = create_client()
    indexer = Indexer(client=client)
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
