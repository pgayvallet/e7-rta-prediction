import asyncio
from commands import fetch_player_list


async def main():
    await fetch_player_list(
        destination_file="./data/users.json",
        num_worker=3,
        max_users=2000,
        initial_recommend_count=5)


asyncio.run(main())
