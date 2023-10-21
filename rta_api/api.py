import aiohttp
from .model import GetRecommendListRecommendedList, GetBattleListResponse

api_base_url = "https://epic7.gg.onstove.com/gameApi"

# https://sandbox-static.smilegatemegaport.com/gameRecord/epic7/epic7_user_world_global.json
# https://sandbox-static.smilegatemegaport.com/gameRecord/epic7/epic7_hero.json

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


### lang -> array of
## code: "c0001",
## grade: "4",
## name: "Mercedes",
## job_cd: "mage",
## attribute_cd: "fire"
## },
###
