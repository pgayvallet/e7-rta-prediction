import typer
import asyncio
import commands
import os
from typing import Annotated

from src import create_client, Indexer, UnitRegistry, ArtefactRegistry
from src.utils import get_user_uuid

# the current RTA season
current_season = 'pvp_rta_ss12'

app = typer.Typer(add_completion=False)


@app.command(name="sync-json")
def sync_jsons():
    async def _sync_jsons():
        await commands.sync_static_lists()

    asyncio.run(_sync_jsons())


@app.command(name="fetch-users")
def fetch_users(
        max_users: Annotated[int, typer.Option(help='The maximum number of users to fetch')] = 500
):
    async def _fetch_users():
        client = create_client()
        try:
            indexer = Indexer(client=client)

            await indexer.create_player_index(season=current_season)

            await commands.fetch_player_list(
                indexer=indexer,
                season=current_season,
                num_worker=3,
                max_users=max_users,
                initial_recommend_count=5)
        finally:
            await client.close()

    asyncio.run(_fetch_users())


@app.command(name="sync-battles")
def sync_battles(
        max_users: Annotated[int, typer.Option(help='The maximum number of users to fetch')] = 1000,
        sync_discovered_players: Annotated[
            bool, typer.Option(help='If true, discovered players will be added to the list')] = True
):
    async def _sync_battles():
        units_file_path = os.path.join(os.getcwd(), "./data/static/units.json")
        unit_registry = UnitRegistry(filepath=units_file_path)

        artefacts_file_path = os.path.join(os.getcwd(), "./data/static/artefacts.json")
        artefact_registry = ArtefactRegistry(filepath=artefacts_file_path)

        client = create_client()
        indexer = Indexer(client=client)

        await indexer.create_player_index(season=current_season)
        await indexer.create_battle_index(season=current_season)

        players = await indexer.get_all_players(season=current_season)
        known_players = set(map(lambda player: get_user_uuid(player.user_id, player.user_world), players))

        players = await indexer.get_users_to_refresh(max_users, current_season)

        await commands.sync_players_battles(
            indexer=indexer,
            unit_registry=unit_registry,
            artefact_registry=artefact_registry,
            season=current_season,
            players_to_sync=players,
            known_player_uuids=known_players,
            sync_discovered_players=sync_discovered_players,
            num_worker=10
        )
        await client.close()

    asyncio.run(_sync_battles())


if __name__ == "__main__":
    app()
