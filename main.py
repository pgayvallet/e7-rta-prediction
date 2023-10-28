import typer
import asyncio
import commands
import os
from src import create_client, Indexer, UnitRegistry, ArtefactRegistry
from typing import Annotated

app = typer.Typer(add_completion=False)

typer.Argument()


@app.command(name="sync-json")
def sync_jsons():
    async def _sync_jsons():
        await commands.sync_static_lists()

    asyncio.run(_sync_jsons())


@app.command(name="fetch-users")
def fetch_users(
        max_users: Annotated[int, typer.Option(help='The maximum number of users to fetch')] = 1000
):
    async def _fetch_users():
        await commands.fetch_player_list(
            destination_file="./data/users.json",
            num_worker=3,
            max_users=max_users,
            initial_recommend_count=5)

    asyncio.run(_fetch_users())


@app.command(name="sync-battles")
def sync_battles(
        max_users: Annotated[int, typer.Option(help='The maximum number of users to fetch')] = 1000
):
    async def _sync_battles():
        units_file_path = os.path.join(os.getcwd(), "./data/static/units.json")
        unit_registry = UnitRegistry(filepath=units_file_path)

        artefacts_file_path = os.path.join(os.getcwd(), "./data/static/artefacts.json")
        artefact_registry = ArtefactRegistry(filepath=artefacts_file_path)

        current_season = 'pvp_rta_ss12'
        client = create_client()
        indexer = Indexer(client=client)

        await indexer.create_player_index(season=current_season)
        await indexer.create_battle_index(season=current_season)

        players = await indexer.get_users_to_refresh(max_users, current_season)

        await commands.sync_players_battles(indexer, unit_registry, artefact_registry, current_season, players,
                                            num_worker=3)
        await client.close()

    asyncio.run(_sync_battles())


if __name__ == "__main__":
    app()
