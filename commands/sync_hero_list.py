import aiohttp
import json
import os
from rta_api import get_hero_list


async def sync_hero_list():
    async with aiohttp.ClientSession() as session:
        response = await get_hero_list(session)
        heroes = {hero.code: hero.model_dump() for hero in response.en}

        with open(os.path.join(os.getcwd(), 'data/static/characters.json'), "w") as target_file:
            target_file.write(json.dumps(heroes, indent=2, ensure_ascii=False))
