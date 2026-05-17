import uuid
from pydantic import BaseModel
from typing import Optional


class ZoneCreate(BaseModel):
    zone_name: str


class ZoneUpdate(BaseModel):
    zone_name: Optional[str] = None


class ZoneOut(BaseModel):
    zone_id: uuid.UUID
    zone_name: str

    model_config = {"from_attributes": True}


class ZoneAssign(BaseModel):
    user_id: uuid.UUID
