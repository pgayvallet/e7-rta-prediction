import asyncio
import aiohttp
import random
import time

base_url = "https://epic7.gg.onstove.com/gameApi"

from rta_api import get_recommended_list


async def worker(name, queue):
    async with aiohttp.ClientSession() as session:
        while True:
            # Get a "work item" out of the queue.
            task = await queue.get()

            print(f'{name} - received task {task}')

            response = await get_recommended_list(session)

            print(f'{name} - task done {response.recommend_list[0].nick_no}')

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


async def main():
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()

    # Generate random timings and put them into the queue.
    total_sleep_time = 0
    for _ in range(20):
        queue.put_nowait({
            "action": "fetch_recommend_list"
        })

    # Create three worker tasks to process the queue concurrently.
    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', queue))
        tasks.append(task)

    # Wait until the queue is fully processed.
    started_at = time.monotonic()
    await queue.join()
    total_slept_for = time.monotonic() - started_at

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    print('====')
    print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
    print(f'total expected sleep time: {total_sleep_time:.2f} seconds')


asyncio.run(main())
