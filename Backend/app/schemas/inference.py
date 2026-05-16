from pydantic import BaseModel
from typing import Optional
import uuid


class PredictionResponse(BaseModel):
    model: str
    label: str
    confidence: float
    incident_created: bool = False
    incident_id: Optional[uuid.UUID] = None


class CombinedPredictionResponse(BaseModel):
    fall_detection: dict
    violence_detection: dict
    incident_created: bool = False
    incidents: Optional[list[dict]] = None  # List of created incidents

