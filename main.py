import asyncio
import commands


async def main():
    """
    await commands.fetch_player_list(
        destination_file="./data/users.json",
        num_worker=3,
        max_users=2000,
        initial_recommend_count=5)
    """

    ## Khhm
    await commands.sync_player_battles(192119856, "world_eu")


asyncio.run(main())
