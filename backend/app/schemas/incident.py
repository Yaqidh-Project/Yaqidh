import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any
from app.models.enums import IncidentCategory, IncidentType


class IncidentCreate(BaseModel):
    danger_category: IncidentCategory
    incident_type: IncidentType
    camera_id: uuid.UUID
    incident_clip: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "open"
    detections: Optional[list[dict[str, Any]]] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    incident_clip: Optional[str] = None
    detections: Optional[list[dict[str, Any]]] = None


class IncidentOut(BaseModel):
    incident_id: uuid.UUID
    timestamp: datetime
    danger_category: str
    incident_type: str
    incident_clip: Optional[str] = None
    status: str
    camera_id: Optional[uuid.UUID] = None
    confidence: Optional[float] = None
    detections: Optional[list[dict[str, Any]]] = None

    model_config = {"from_attributes": True}
