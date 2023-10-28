import aiohttp
import json
import os
from rta_api import get_hero_list, get_artifact_list


async def sync_static_lists():
    print("Syncing unit list...")
    await sync_unit_list()
    print("Syncing artefact list...")
    await sync_artefact_list()
    print("Done.")


async def sync_unit_list():
    async with aiohttp.ClientSession() as session:
        response = await get_hero_list(session)

        def map_hero(hero):
            return (
                hero.code,
                {
                    "id": hero.code,
                    "name": hero.name,
                    "grade": hero.grade,
                    "role": hero.job_cd,
                    "element": hero.attribute_cd,
                }
            )

        heroes = dict(map(map_hero, response.en))

        target_file_path = os.path.join(os.getcwd(), 'data/static/units.json')
        with open(target_file_path, "w") as target_file:
            target_file.write(json.dumps(heroes, indent=2, ensure_ascii=False))


async def sync_artefact_list():
    async with aiohttp.ClientSession() as session:
        response = await get_artifact_list(session)

        def map_hero(artefact):
            return (
                artefact.code,
                {
                    "id": artefact.code,
                    "name": artefact.name,
                }
            )

        artefacts = dict(map(map_hero, response.en))

        target_file_path = os.path.join(os.getcwd(), 'data/static/artefacts.json')
        with open(target_file_path, "w") as target_file:
            target_file.write(json.dumps(artefacts, indent=2, ensure_ascii=False))
