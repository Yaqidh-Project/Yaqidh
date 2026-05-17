import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any
from app.schemas.incident import IncidentOut
from app.models.enums import IncidentCategory


class ReportFilterCriteria(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    danger_category: Optional[IncidentCategory] = None
    status: Optional[str] = None
    camera_id: Optional[uuid.UUID] = None


class ReportCreate(BaseModel):
    filter_criteria: Optional[dict[str, Any]] = None


class ReportOut(BaseModel):
    report_id: uuid.UUID
    generated_at: datetime
    filter_criteria: Optional[dict[str, Any]] = None
    report_summary: Optional[str] = None
    user_id: uuid.UUID
    incidents: list[IncidentOut] = []

    model_config = {"from_attributes": True}
