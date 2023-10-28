import aiohttp
import random
from .model import GetRecommendListRecommendedList, GetBattleListResponse, HeroList, ArtefactList

api_base_url = "https://epic7.gg.onstove.com/gameApi"
static_assets_url = "https://static.smilegatemegaport.com"


# https://sandbox-static.smilegatemegaport.com/gameRecord/epic7/epic7_user_world_global.json
# https://sandbox-static.smilegatemegaport.com/gameRecord/epic7/epic7_hero.json
# https://sandbox-static.smilegatemegaport.com/event/qa/epic7/guide/images/hero/c1133_s.png

async def get_recommended_list(session: aiohttp.ClientSession) -> "GetRecommendListRecommendedList":
    async with session.post(f'{api_base_url}/getRecommendList') as request:
        response = await request.json()
        parsed = GetRecommendListRecommendedList(**response["result_body"])
        return parsed


async def get_battle_list(session: aiohttp.ClientSession, user_id: int, world_code: str,
                          lang: str = "en", season_code: str = "") -> "GetBattleListResponse":
    params = {
        "nick_no": user_id,
        "world_code": world_code,
        "lang": lang,
        "season_code": season_code,
    }
    async with session.post(f'{api_base_url}/getBattleList', params=params) as request:
        response = await request.json()
    parsed = GetBattleListResponse(**response)
    return parsed


async def get_hero_list(session: aiohttp.ClientSession) -> "HeroList":
    cache_buster = random.randrange(100000)
    async with session.get(f'{static_assets_url}/gameRecord/epic7/epic7_hero.json?_={cache_buster}') as request:
        response = await request.json()
        parsed = HeroList(**response)
        return parsed


async def get_artifact_list(session: aiohttp.ClientSession) -> "ArtefactList":
    async with session.get(f'{static_assets_url}/gameRecord/epic7/epic7_artifact.json') as request:
        response = await request.json()
    parsed = ArtefactList(**response)
    return parsed
