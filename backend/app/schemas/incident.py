import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any, Union
from app.models.enums import IncidentCategory, IncidentType


class IncidentCreate(BaseModel):
    danger_category: IncidentCategory
    incident_type: IncidentType
    camera_id: uuid.UUID
    incident_clip: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "open"
    detections: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    incident_clip: Optional[str] = None
    detections: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None


class IncidentOut(BaseModel):
    incident_id: uuid.UUID
    timestamp: datetime
    danger_category: str
    incident_type: str
    incident_clip: Optional[str] = None
    status: str
    camera_id: Optional[uuid.UUID] = None
    confidence: Optional[float] = None
    detections: Optional[Union[dict[str, Any], list[dict[str, Any]]]] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = None
    zone_name: Optional[str] = None  # Added: resolved via camera → zone relationship

    model_config = {"from_attributes": True}

    @classmethod
    def from_incident(cls, incident) -> "IncidentOut":
        zone_name = None
        if incident.camera and incident.camera.zone:
            zone_name = incident.camera.zone.zone_name
        return cls(
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,
            danger_category=incident.danger_category,
            incident_type=incident.incident_type,
            incident_clip=incident.incident_clip,
            status=incident.status,
            camera_id=incident.camera_id,
            confidence=incident.confidence,
            detections=incident.detections,
            resolved_at=incident.resolved_at,
            resolved_by_id=incident.resolved_by_id,
            zone_name=zone_name,
        )