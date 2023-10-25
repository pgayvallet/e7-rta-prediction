import pydantic
from typing import Optional


class RtaPlayer(pydantic.BaseModel):
    user_id: int
    user_world: str
    user_name: str
    last_known_rank: str
    last_update_time: Optional[int] = None
    last_updated_battle_id: Optional[int] = None
