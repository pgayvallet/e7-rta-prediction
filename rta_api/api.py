import aiohttp
from .model import GetRecommendListRecommendedList

base_url = "https://epic7.gg.onstove.com/gameApi"


async def get_recommended_list(session: aiohttp.ClientSession) -> "GetRecommendListRecommendedList":
    async with session.post(f'{base_url}/getRecommendList') as request:
        response = await request.json()
        parsed = GetRecommendListRecommendedList(**response["result_body"])
        return parsed
