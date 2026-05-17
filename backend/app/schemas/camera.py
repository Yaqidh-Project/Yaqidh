import uuid
from pydantic import BaseModel
from typing import Optional
from app.models.enums import CameraStatus


class CameraCreate(BaseModel):
    camera_name: str
    camera_type: str = "IP"
    stream_url: str
    ip_address: Optional[str] = None
    status: CameraStatus = CameraStatus.Active
    zone_id: uuid.UUID


class CameraUpdate(BaseModel):
    camera_name: Optional[str] = None
    camera_type: Optional[str] = None
    stream_url: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[CameraStatus] = None
    zone_id: Optional[uuid.UUID] = None


class CameraOut(BaseModel):
    camera_id: uuid.UUID
    camera_name: str
    camera_type: str
    stream_url: str
    ip_address: Optional[str] = None
    status: str
    zone_id: uuid.UUID

    model_config = {"from_attributes": True}
