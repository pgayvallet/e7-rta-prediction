import pydantic
from typing import Optional


class RtaPlayer(pydantic.BaseModel):
    user_id: int
    user_world: str
    user_name: str
    last_known_rank: str
    last_update_time: Optional[int] = None
    last_updated_battle_id: Optional[int] = None


rta_player_mappings = {
    "dynamic": "strict",
    "properties": {
        "user_id": {"type": "long"},
        "user_world": {"type": "keyword"},
        "user_name": {"type": "keyword"},
        "last_known_rank": {"type": "keyword"},
        "last_update_time": {"type": "date"},
        "last_updated_battle_id": {"type": "long"},
    }
}
